"""
Extract Skills — ใช้ Ollama (llama3) แยก skills จาก Job Description
"""
import json
import re
from itertools import chain
import ollama as ollama_client
from etl.config import OLLAMA_MODEL

SYSTEM_PROMPT = """You are a Job Description analyzer. Extract structured information from the given Job Description.
Return ONLY a valid JSON object with these fields:
- "required_skills": array of technical skills/tools (e.g., ["Python", "SQL", "AWS", "Airflow"])
- "experience_years": string describing required experience (e.g., "3-5 years", "5+ years", "Not specified")
- "job_type": one of "Full-time", "Contract", "Internship", "Part-time", or "Not specified"

Rules:
- Include programming languages, frameworks, databases, cloud services, tools
- Normalize skill names (e.g., "Postgres" → "PostgreSQL", "JS" → "JavaScript")
- If a field is not mentioned in the JD, use "Not specified"
- Return ONLY the JSON, no explanations"""


def extract_skills(jd_text: str, model: str = None) -> dict:
    """
    ส่ง JD text ไปให้ Ollama แยก skills ออกมาเป็น JSON
    
    Returns:
        dict with keys: required_skills, experience_years, job_type
    """
    if not jd_text or jd_text.strip() in ("", "Not Found", "Error", "No Link"):
        return {
            "required_skills": [],
            "experience_years": "Not specified",
            "job_type": "Not specified",
        }

    model = model or OLLAMA_MODEL

    user_prompt = f"""Analyze this Job Description and extract the required information:

    {jd_text[:8000]}"""  # ตัดไม่เกิน 8000 ตัวอักษร เพื่อความเร็ว

    try:
        response = ollama_client.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.1},  # ลด randomness เพื่อให้ output คงที่
        )

        content = response['message']['content'].strip()
        
        # พยายาม parse JSON จาก response
        parsed = _parse_json_response(content)
        
        # Flatten skills (กัน Ollama คืน nested array)
        parsed['required_skills'] = _flatten_skills(parsed.get('required_skills', []))
        
        return parsed

    except Exception as e:
        print(f"   ⚠️ Ollama error: {e}")
        return {
            "required_skills": [],
            "experience_years": "Not specified",
            "job_type": "Not specified",
        }


def _flatten_skills(skills) -> list[str]:
    """Flatten nested list เป็น flat list of strings
    เช่น [['Python','SQL'],['AWS']] → ['Python','SQL','AWS']
    """
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
    """ลบ JS-style comments ออกจาก JSON text (// ... และ /* ... */)"""
    # ลบ // single-line comments (ระวังไม่ลบ :// ใน URLs)
    text = re.sub(r'(?<!:)//.*?(?=\n|$)', '', text)
    # ลบ /* block comments */
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text


def _parse_json_response(text: str) -> dict:
    """พยายาม parse JSON จาก LLM response (อาจมี markdown wrapper หรือ comments)"""
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

    # ลบ comments แล้วลองใหม่
    cleaned = _strip_json_comments(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # ลองหา JSON block ใน ```json ... ```
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(_strip_json_comments(match.group(1)))
        except json.JSONDecodeError:
            pass

    # ลองหา { ... } ตัวแรก
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # ถ้า parse ไม่ได้เลย
    print(f"   ⚠️ ไม่สามารถ parse JSON: {text[:200]}...")
    return default

