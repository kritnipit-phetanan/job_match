from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import resume, analytics

app = FastAPI(
    title="JobMatcher API",
    version="1.0.0",
    description="Resume Matching & Cover Letter Generator API"
)

# CORS — อ่าน origins จาก env (comma-separated), default: localhost
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)
app.include_router(resume.router)
app.include_router(analytics.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "JobMatcher Brain is running!",
    }