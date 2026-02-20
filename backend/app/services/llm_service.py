from google import genai
from app.core.config import settings
import json

# 1. ตั้งค่า API Key จากไฟล์ .env
client = genai.Client(api_key=settings.GEMINI_API_KEY)

def generate_tailored_cover_letter(resume_text: str, job_desc: str) -> str:
    """
    ส่ง Resume และ Job Description ให้ Gemini เขียน Cover Letter
    """
    try:
        # ใช้รุ่น Flash เพราะเร็วกว่าและฉลาดเพียงพอสำหรับงานเขียน
        model = 'gemini-3-flash-preview'
        
        # 2. ออกแบบ System Prompt (Prompt Engineering)
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

        # 3. สั่งให้ Gemini สร้างเนื้อหา
        response = client.models.generate_content(model=model, contents=prompt)
        
        return response.text

    except Exception as e:
        print(f"⚠️ Gemini API Error: {e}")
        raise ValueError("ไม่สามารถสร้าง Cover Letter ได้ กรุณาตรวจสอบ API Key หรือการเชื่อมต่อ")

def analyze_skill_gap(resume_text: str, job_skills: list[str]) -> dict:
    """
    ให้ Gemini เทียบ Resume กับ Job Skills แล้วแยกเป็น หมวดหมู่ (มี/ขาด)
    """
    try:
        model = 'gemini-3-flash-preview'
        
        # บังคับให้ AI คืนค่ามาเป็น JSON ที่เรากำหนดไว้เป๊ะๆ
        prompt = f"""
        You are an expert technical recruiter. Compare the candidate's resume with the REQUIRED JOB SKILLS.

        CANDIDATE RESUME:
        {resume_text}

        REQUIRED JOB SKILLS:
        {job_skills}

        Categorize EVERY skill from the REQUIRED JOB SKILLS list into either 'matched_skills' (candidate has it or has related experience) or 'missing_skills' (candidate lacks it).
        Respond ONLY with a valid JSON object in this exact format, without any markdown formatting or explanation:
        {{
            "matched_skills": ["skill1", "skill2"],
            "missing_skills": ["skill3"]
        }}
        """
        
        response = client.models.generate_content(model=model, contents=prompt)
        text = response.text.strip()
        
        # ป้องกันกรณี Gemini ส่ง ```json ... ``` กลับมา
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
                
        return json.loads(text.strip())
        
    except Exception as e:
        print(f"⚠️ Skill Gap API Error: {e}")
        raise ValueError("ไม่สามารถวิเคราะห์ Skill Gap ได้ในขณะนี้")