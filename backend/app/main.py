from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title="JobMatcher API",
    version="1.0.0",
    description="Resume Matching & Cover Letter Generator API"
)

@app.get("/")
def read_root():
    print(f"กำลังเชื่อมต่อ Database ที่: {settings.DB_HOST}")
    return {
        "status": "online",
        "message": "JobMatcher Brain is running! 🧠",
        "database_host": settings.DB_HOST # ทดสอบว่าอ่าน config ได้ไหม
    }