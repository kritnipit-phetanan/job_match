import psycopg2
from app.core.config import settings

def get_db_connection():
    """
    สร้าง Connection ไปยัง PostgreSQL
    รองรับทั้ง DATABASE_URL (Supabase) และ individual vars (Local Docker)
    """
    if settings.DATABASE_URL:
        conn = psycopg2.connect(settings.DATABASE_URL)
    else:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
    try:
        yield conn
    finally:
        conn.close()