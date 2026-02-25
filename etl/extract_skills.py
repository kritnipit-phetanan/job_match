"""
Extract Skills — ใช้ Groq API (llama-3.1-8b-instant) แยก skills จาก Job Description
"""
import json
import re
import time
from groq import Groq, RateLimitError
from etl.config import GROQ_API_KEY, GROQ_MODEL

# Rate limiting — Groq free tier: 6000 TPM (tokens per minute)
# แต่ละ call ใช้ ~600 tokens → ยิงได้ ~10 call/min → delay ≥ 12s ต่อ call
_DELAY_BETWEEN_CALLS = 12   # วินาที ระหว่างแต่ละ call (เพิ่มจาก 3 เป็น 12 เพื่อไม่ให้ชน TPM limit)
_MAX_RETRIES = 5            # จำนวนครั้งที่ retry ถ้าเจอ 429
_RETRY_BASE_DELAY = 15      # วินาที เริ่มต้น (exponential backoff: 15, 30, 60, ...)

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
    ส่ง JD text ไปให้ Groq (llama-3.1-8b-instant) แยก skills ออกมาเป็น JSON
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
            # Parse เวลาจาก error message โดยตรง เช่น "Please try again in 4.43s"
            wait_time = None
            error_msg = str(e)
            match = re.search(r'try again in (\d+\.?\d*)s', error_msg)
            if match:
                wait_time = float(match.group(1)) + 1  # +1s buffer เผื่อ

            if not wait_time:
                wait_time = _RETRY_BASE_DELAY * (2 ** attempt)  # fallback: 10, 20, 40...

            print(f"   ⏳ Rate limited (429). รอ {wait_time:.1f}s แล้ว retry ({attempt+1}/{_MAX_RETRIES})...")
            time.sleep(wait_time)
            continue

        except Exception as e:
            # Error อื่นๆ ไม่ต้อง retry
            print(f"   ⚠️ Groq API error: {e}")
            break

    # retry หมดแล้วยังไม่ได้ → return default
    print(f"   ❌ Groq API failed after {_MAX_RETRIES} retries")
    return {
        "required_skills": [],
        "experience_years": "Not specified",
        "job_type": "Not specified",
    }


def _flatten_skills(skills) -> list[str]:
    """Flatten nested list เป็น flat list of strings"""
    if not skills:
        return []
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
