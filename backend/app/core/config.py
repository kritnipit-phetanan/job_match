from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# .env อยู่ที่ root ของโปรเจกต์ (parent ของ backend/)
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"

class Settings(BaseSettings):
    # Database — รองรับทั้ง Supabase (DATABASE_URL) และ Local Docker (individual vars)
    DATABASE_URL: Optional[str] = None  # Supabase / Cloud
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "jobmatcher"
    DB_USER: str = "jobmatcher"
    DB_PASSWORD: str = ""

    # AI Config
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # CORS — อนุญาต origins (comma-separated)
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def database_url(self) -> str:
        """ถ้ามี DATABASE_URL ให้ใช้เลย ถ้าไม่มีก็ build จาก individual vars"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"

settings = Settings()