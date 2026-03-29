"""
RAG Service — Embedding + Vector Search
ใช้ Gemini Embedding API (gemini-embedding-001)
"""
from google import genai
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings

# Lazy-init Gemini Client (ไม่ crash ตอน import ถ้ายังไม่มี API key)
_embed_client = None

def _get_embed_client():
    global _embed_client
    if _embed_client is None:
        _embed_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _embed_client

def embed_text(text: str) -> list[float]:
    """
    ใช้ Gemini Embedding API แปลงข้อความ Resume เป็น Vector (768 dims)
    """
    try:
        client = _get_embed_client()
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text[:8000],
            config={"output_dimensionality": 768}
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"⚠️ Gemini Embedding Error: {e}")
        raise ValueError("ไม่สามารถสร้าง Vector จาก Resume ได้ ตรวจสอบ GEMINI_API_KEY")


def search_matching_jobs(
    conn, 
    resume_vector: list[float], 
    pool_size: int = 20,
    location_filter: str = None,
    job_type_filter: str = None
) -> list[dict]:
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        base_query = """
            SELECT 
                j.id, j.title, j.company, j.location, j.salary, j.link, j.skills,
                j.experience_years, j.job_type, j.description,
                ROUND((1 - (e.embedding <=> %s::vector))::numeric * 100, 2) AS match_score
            FROM jobs j
            JOIN job_embeddings e ON j.id = e.job_id
            WHERE e.is_active = true
        """
        
        vector_str = str(resume_vector)
        params = [vector_str]

        if location_filter:
            base_query += " AND j.location ILIKE %s"
            params.append(f"%{location_filter}%")
        if job_type_filter and job_type_filter.lower() != "not specified":
            base_query += " AND j.job_type ILIKE %s"
            params.append(f"%{job_type_filter}%")

        base_query += " ORDER BY e.embedding <=> %s::vector LIMIT %s"
        params.extend([vector_str, pool_size])

        cur.execute(base_query, params)
        return cur.fetchall()

    except Exception as e:
        print(f"⚠️ Database Search Error: {e}")
        raise ValueError("เกิดข้อผิดพลาดในการค้นหาข้อมูล")
    finally:
        cur.close()