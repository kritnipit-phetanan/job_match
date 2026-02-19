import google.genai as genai
from app.core.config import settings

# 1. ตั้งค่า API Key จากไฟล์ .env
genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_tailored_cover_letter(resume_text: str, job_desc: str) -> str:
    """
    ส่ง Resume และ Job Description ให้ Gemini เขียน Cover Letter
    """
    try:
        # ใช้รุ่น Flash เพราะเร็วกว่าและฉลาดเพียงพอสำหรับงานเขียน
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
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
        response = model.generate_content(prompt, stream=True)
        
        return response.text

    except Exception as e:
        print(f"⚠️ Gemini API Error: {e}")
        raise ValueError("ไม่สามารถสร้าง Cover Letter ได้ กรุณาตรวจสอบ API Key หรือการเชื่อมต่อ")