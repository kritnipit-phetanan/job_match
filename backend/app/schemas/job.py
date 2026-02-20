from pydantic import BaseModel, Field

class CoverLetterRequest(BaseModel):
    resume_markdown: str = Field(..., description="ข้อความ Resume (Markdown) ที่ได้จากการ Parse")
    job_description: str = Field(..., description="รายละเอียดงาน (Job Description) ที่ต้องการสมัคร")

class SkillGapRequest(BaseModel):
    resume_markdown: str = Field(..., description="ข้อความ Resume (Markdown)")
    job_skills: list[str] = Field(..., description="รายการสกิลที่งานนั้นต้องการ")