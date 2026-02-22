from google import genai
from google.genai.errors import APIError
from app.core.config import settings
import json
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

# 1. ตั้งค่า API Key จากไฟล์ .env
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# โมเดลหลัก และโมเดลสำรอง
MODELS = ['gemini-3-flash-preview', 'gemini-2.5-flash']

@retry(
    stop=stop_after_attempt(3), # ลองซ้ำสูงสุด 3 ครั้ง
    wait=wait_exponential(multiplier=1, min=2, max=10), # รอ 2, 4, 8 วินาที
    retry=retry_if_exception_type(APIError), # ลองใหม่เฉพาะกรณี API มีปัญหา (เช่น 503)
    reraise=True
)
def generate_tailored_cover_letter(resume_text: str, job_desc: str) -> str:
    """
    ส่ง Resume และ Job Description ให้ Gemini เขียน Cover Letter
    มีกลไก Retry + Fallback Model
    """
    prompt = f"""
    You are an expert Career Coach and Professional Copywriter.
    Your task is to write a highly tailored, professional, and compelling Cover Letter.

    CANDIDATE'S RESUME:
    {resume_text}

    TARGET JOB DESCRIPTION:
    {job_desc}

    RULES & GUIDELINES:
    1. Keep it concise (3-4 paragraphs maximum).
    2. Tone: Professional, confident, and enthusiastic.
    3. Match the Candidate's skills/experiences DIRECTLY with the requirements in the Job Description.
    4. DO NOT invent or fabricate any skills, experiences, or metrics that are not in the resume.
    5. If personal details (like phone/email) are missing or marked as [PHONE]/[EMAIL], use placeholders like "[Your Phone Number]".
    6. Start directly with "Dear Hiring Manager," and end with a professional closing. Do not include sender/recipient addresses at the top.
    """

    for model in MODELS:
        try:
            # 3. สั่งให้ Gemini สร้างเนื้อหา
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text
        except APIError as e:
            logger.warning(f"⚠️ Model {model} failed with API Error: {e}")
            if e.code == 503 and model != MODELS[-1]:
                logger.info(f"🔄 Switching to fallback model...")
                continue # ลองโมเดลถัดไป
            raise # ถ้าเป็น error อื่นๆ หรือรันมาจนถึงโมเดลสุดท้ายแล้ว ให้โยน error ออกไปให้ Tenacity จัดการ retry
        except Exception as e:
            logger.error(f"⚠️ Unexpected Error generating Cover Letter: {e}")
            raise ValueError("ไม่สามารถสร้าง Cover Letter ได้ กรุณาตรวจสอบ API Key หรือการเชื่อมต่อ")

    raise ValueError("All models failed to generate Cover Letter.")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(APIError),
    reraise=True
)
def analyze_batch_resume(resume_text: str, jobs_list: list[dict]) -> dict:
    """
    ยิง Gemini ครั้งเดียว เพื่อหา "อายุงานรวม" และ "Skill Gap" ของงานทั้ง 20 งาน
    """

    # คัดมาเฉพาะข้อมูลที่จำเป็นส่งให้ AI (ลดจำนวน Token)
    simplified_jobs = [
        {"id": job["id"], "skills": job["skills"]} 
        for job in jobs_list if job.get("skills")
    ]

    prompt = f"""
    You are an expert technical recruiter. Analyze the CANDIDATE RESUME and a list of TARGET JOBS.

    Tasks:
    1. Calculate the candidate's TOTAL years of professional work experience as an integer.
    2. For EACH job in the TARGET JOBS list, categorize its required skills into 'matched' (candidate has it) or 'missing' (candidate lacks it).

    CANDIDATE RESUME:
    {resume_text}

    TARGET JOBS:
    {json.dumps(simplified_jobs)}

    IMPORTANT: Use the EXACT numeric "id" from each job as the key in "skill_gaps".
    Respond ONLY with a valid JSON in this exact format:
    {{
        "years_of_experience": 2,
        "skill_gaps": {{
            "101": {{"matched": ["Python", "SQL"], "missing": ["Spark"]}},
            "102": {{"matched": ["AWS"], "missing": ["Docker", "K8s"]}}
        }}
    }}
    """
    
    for model in MODELS:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            text = response.text.strip()
            
            # ป้องกันกรณี Gemini ส่ง ```json ... ``` กลับมา
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            result = json.loads(text.strip())
            logger.info(f"✅ Skill Gap keys from AI: {list(result.get('skill_gaps', {}).keys())[:5]}")
            return result
            
        except APIError as e:
            logger.warning(f"⚠️ Model {model} failed with API Error: {e}")
            if e.code == 503 and model != MODELS[-1]:
                logger.info(f"🔄 Switching to fallback model...")
                continue
            raise
        except Exception as e:
            logger.error(f"⚠️ Batch Analysis Error: {e}")
            raise ValueError({"years_of_experience": 0, "skill_gaps": {}})

    raise ValueError("All models failed to analyze Skill Gap.")