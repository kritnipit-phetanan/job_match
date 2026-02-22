"""
ETL Config — โหลด .env และจัดการ connection กับ DB + AI APIs
"""
import os
from dotenv import load_dotenv

# โหลด .env จาก root ของโปรเจกต์
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Database — รองรับทั้ง DATABASE_URL (Supabase) และ individual vars (Local)
DATABASE_URL = os.getenv('DATABASE_URL', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'jobmatcher')
DB_USER = os.getenv('DB_USER', 'jobmatcher')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'jobmatcher_secret')

def get_database_url() -> str:
    """ถ้ามี DATABASE_URL ให้ใช้เลย ถ้าไม่มีก็ build จาก individual vars"""
    if DATABASE_URL:
        return DATABASE_URL
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# AI APIs
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FULL_DATA = os.path.join(PROJECT_ROOT, 'jobsdb_full_data.csv')
