"""
Extract Skills — ใช้ Groq API (GROQ_MODEL ใน etl/config.py) แยก skills จาก Job Description
"""
import json
import re
import time
from groq import Groq, RateLimitError, APIConnectionError, InternalServerError
from etl.config import GROQ_API_KEY, GROQ_MODEL

# Rate limiting — Groq free tier (qwen/qwen3.8-27b): 1000 req/วัน, 8000 TPM,
# และ output 1000 tokens/min (OTPM) ซึ่งตึงสุด — output ~200 tokens/call → ~5 call/min
_DELAY_BETWEEN_CALLS = 12   # วินาที ระหว่างแต่ละ call
_MAX_RETRIES = 5            # จำนวนครั้งที่ retry ถ้าเจอ 429
_RETRY_BASE_DELAY = 15      # วินาที เริ่มต้น (exponential backoff: 15, 30, 60, ...)


class SkillExtractionUnavailable(Exception):
    """Groq ใช้งานไม่ได้ (model ถูกถอด / key ผิด / retry หมด) — ห้ามบันทึก skills ว่างแทน"""


class DailyLimitReached(SkillExtractionUnavailable):
    """โควตา requests/วัน ของ Groq หมด — หยุดแล้วให้รอบถัดไปทำต่อ"""


def _retry_after_seconds(msg: str):
    """ดึงเวลารอจาก 'Please try again in 1m26.4s' หรือ '3.48s'"""
    m = re.search(r'try again in (?:(\d+)h\s*)?(?:(\d+)m\s*)?(\d+(?:\.\d+)?)s', msg)
    if not m:
        return None
    h, mnt, s = m.groups()
    return int(h or 0) * 3600 + int(mnt or 0) * 60 + float(s)

SYSTEM_PROMPT = """You are a Job Description analyzer. Extract structured information from the given Job Description.
Return ONLY a valid JSON object with these fields:
- "required_skills": array of skills (e.g., ["Python", "SQL", "Lean", "AutoCAD", "Project Management"])
- "experience_years": string describing required experience (e.g., "3-5 years", "5+ years", "Not specified")
- "job_type": one of "Full-time", "Contract", "Internship", "Part-time", or "Not specified"

Rules:
- Extract ALL types of skills mentioned or implied in the JD, including but not limited to:
  • Programming languages, frameworks, databases, cloud services
  • Engineering tools (AutoCAD, SolidWorks, PLC, SCADA, SAP, etc.)
  • Methodologies (Lean, Six Sigma, Kaizen, 5S, Agile, Scrum, etc.)
  • Certifications & standards (ISO, PMP, CFA, etc.)
  • Domain skills (Quality Control, Preventive Maintenance, Calibration, etc.)
  • Management skills (Team Leadership, Project Management, Production Planning, etc.)
- Normalize skill names (e.g., "Postgres" → "PostgreSQL", "JS" → "JavaScript")
- If a field is not mentioned in the JD, use "Not specified"
- Return ONLY the JSON object, nothing else
- Do NOT add any comments, annotations, or notes inside the JSON
- Do NOT add parenthetical remarks like (implied) or (assumed) after values
- Every value in the arrays must be a plain string with no extra text"""


def extract_skills(jd_text: str, model: str = None) -> dict:
    """
    ส่ง JD text ไปให้ Groq แยก skills ออกมาเป็น JSON
    พร้อม retry + exponential backoff สำหรับ 429 Rate Limit
    """
    if not jd_text or jd_text.strip() in ("", "Not Found", "Error", "No Link"):
        return {
            "required_skills": [],
            "experience_years": "Not specified",
            "job_type": "Not specified",
        }

    model = model or GROQ_MODEL

    user_prompt = f"""Analyze this Job Description and extract the required information:

    {jd_text[:8000]}"""

    # ปิด SDK built-in retry เพื่อจัดการ 429 เอง
    client = Groq(api_key=GROQ_API_KEY, max_retries=0)

    for attempt in range(_MAX_RETRIES):
        try:
            # Baseline delay ทุก call เพื่อไม่ให้ยิงถี่เกินไป
            time.sleep(_DELAY_BETWEEN_CALLS)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )

            content = response.choices[0].message.content.strip()
            parsed = _parse_json_response(content)
            parsed['required_skills'] = _flatten_skills(parsed.get('required_skills', []))
            return parsed

        except RateLimitError as e:
            error_msg = str(e)
            if "per day" in error_msg:
                raise DailyLimitReached(error_msg) from e

            # Parse เวลาจาก error message โดยตรง เช่น "Please try again in 4.43s"
            wait_time = _retry_after_seconds(error_msg)
            wait_time = wait_time + 1 if wait_time else _RETRY_BASE_DELAY * (2 ** attempt)

            print(f"   ⏳ Rate limited (429). รอ {wait_time:.1f}s แล้ว retry ({attempt+1}/{_MAX_RETRIES})...")
            time.sleep(wait_time)
            continue

        except (APIConnectionError, InternalServerError) as e:
            # เน็ตหลุด / timeout / Groq 5xx — ชั่วคราว รอแล้วลองใหม่
            wait_time = _RETRY_BASE_DELAY * (2 ** attempt)
            print(f"   🌐 เชื่อมต่อ Groq ไม่ได้ ({type(e).__name__}). รอ {wait_time}s แล้ว retry ({attempt+1}/{_MAX_RETRIES})...")
            time.sleep(wait_time)
            continue

        except Exception as e:
            # เช่น model ถูกถอด (404), key ผิด (401) — retry ไปก็ไม่หาย
            raise SkillExtractionUnavailable(f"Groq API error ({model}): {e}") from e

    raise SkillExtractionUnavailable(f"Groq API ยังใช้ไม่ได้หลัง retry {_MAX_RETRIES} ครั้ง")


def _flatten_skills(skills) -> list[str]:
    """Flatten nested list เป็น flat list of strings"""
    if not skills:
        return []
    # บาง model ตอบเป็น string เช่น "Not specified" — ถ้าวน list ตรง ๆ จะแตกเป็นตัวอักษร
    if isinstance(skills, str):
        return [] if skills.strip().lower() in ("not specified", "none", "n/a") else [skills]
    flat = []
    for item in skills:
        if isinstance(item, list):
            flat.extend(str(s) for s in item)
        else:
            flat.append(str(item))
    return flat


def _strip_json_comments(text: str) -> str:
    """ลบ JS-style comments ออกจาก JSON text"""
    text = re.sub(r'(?<!:)//.*?(?=\n|$)', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text


def _clean_llm_json(text: str) -> str:
    """
    ลบ inline comments ที่ LLM ชอบแทรกใน JSON เช่น:
      "AWS" (implied, but not explicitly mentioned),
    → "AWS",
    """
    # ลบ (parenthetical comments) ที่อยู่หลัง quoted string
    text = re.sub(r'"\s*\([^)]*\)', '"', text)
    # ลบ trailing comma ก่อน ] (JSON ไม่อนุญาต)
    text = re.sub(r',\s*]', ']', text)
    return text


def _parse_json_response(text: str) -> dict:
    """พยายาม parse JSON จาก LLM response"""
    default = {
        "required_skills": [],
        "experience_years": "Not specified",
        "job_type": "Not specified",
    }

    # ลอง parse ตรงๆ ก่อน
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # ลบ comments + inline annotations แล้วลองใหม่
    cleaned = _clean_llm_json(_strip_json_comments(text))
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # ลอง extract จาก code block
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(_clean_llm_json(_strip_json_comments(match.group(1))))
        except json.JSONDecodeError:
            pass

    # ลอง regex หา JSON object
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(_clean_llm_json(match.group(0)))
        except json.JSONDecodeError:
            pass

    print(f"   ⚠️ ไม่สามารถ parse JSON: {text[:200]}...")
    return default
