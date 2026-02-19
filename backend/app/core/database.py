import psycopg2
from app.core.config import settings

def get_db_connection():
    """
    สร้าง Connection ไปยัง PostgreSQL
    FastAPI จะเรียกใช้ function นี้เมื่อมี Request เข้ามา
    """
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
        conn.close() # ปิด Connection เสมอเมื่อจบ Request