from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import resume, analytics

app = FastAPI(
    title="JobMatcher API",
    version="1.0.0",
    description="Resume Matching & Cover Letter Generator API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.1.2:3000"], # อนุญาตทั้ง Local และ IP ตรง
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)
app.include_router(resume.router)
app.include_router(analytics.router)

@app.get("/")
def read_root():
    print(f"กำลังเชื่อมต่อ Database ที่: {settings.DB_HOST}")
    return {
        "status": "online",
        "message": "JobMatcher Brain is running! 🧠",
        "database_host": settings.DB_HOST # ทดสอบว่าอ่าน config ได้ไหม
    }