import ollama
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings

def embed_text(text: str) -> list[float]:
    """
    เรียกใช้ Ollama (nomic-embed-text) เพื่อแปลงข้อความ Resume เป็น Vector
    """
    try:
        # กำหนด Base URL ตาม config
        client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        
        # ส่งข้อความไป Embed (จำกัดความยาวเพื่อไม่ให้เกิน Context Window ของ Nomic)
        response = client.embed(
            model="nomic-embed-text",
            input=text[:8000] 
        )
        return response['embeddings'][0]
    except Exception as e:
        print(f"⚠️ Vector Embedding Error: {e}")
        raise ValueError("ไม่สามารถสร้าง Vector จาก Resume ได้ ตรวจสอบว่า Ollama รันอยู่หรือไม่")

def search_matching_jobs(
    conn, 
    resume_vector: list[float], 
    pool_size: int = 20, # <-- ดึงมาเผื่อเลย 20 งาน
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
            WHERE 1=1
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

# def search_matching_jobs(
#     conn, 
#     resume_vector: list[float], 
#     limit: int = 5,
#     location_filter: str = None,
#     job_type_filter: str = None
# ) -> list[dict]:
#     """
#     ค้นหางานที่ตรงกับ Resume Vector มากที่สุดจาก PostgreSQL (pgvector)
#     พร้อมคำนวณ Match Score (%)
#     """
#     # ใช้ RealDictCursor เพื่อให้ผลลัพธ์จาก DB ออกมาเป็น Dictionary (JSON-ready)
#     cur = conn.cursor(cursor_factory=RealDictCursor)

#     try:
#         # สร้าง SQL Query พื้นฐาน
#         # ใช้ <=> ใน pgvector เพื่อหา Cosine Distance
#         # Similarity = 1 - Cosine Distance
#         base_query = """
#             SELECT 
#                 j.id, 
#                 j.title, 
#                 j.company, 
#                 j.location, 
#                 j.salary, 
#                 j.link, 
#                 j.skills,
#                 j.experience_years,
#                 j.job_type,
#                 ROUND((1 - (e.embedding <=> %s::vector))::numeric * 100, 2) AS match_score
#             FROM jobs j
#             JOIN job_embeddings e ON j.id = e.job_id
#             WHERE 1=1
#         """
        
#         # ตัวแปรที่จะส่งเข้าไปแทนที่ %s ใน SQL
#         # แปลง list ของ float เป็น string format ที่ pgvector เข้าใจ: '[0.1, 0.2, ...]'
#         vector_str = str(resume_vector)
#         params = [vector_str]

#         # --- ส่วนของ Hybrid Search (เพิ่ม Filter ด้วย SQL ธรรมดา) ---
#         if location_filter:
#             base_query += " AND j.location ILIKE %s"
#             params.append(f"%{location_filter}%")
            
#         if job_type_filter and job_type_filter.lower() != "not specified":
#             base_query += " AND j.job_type ILIKE %s"
#             params.append(f"%{job_type_filter}%")

#         # --- ส่วนของการจัดเรียงและจำกัดจำนวน ---
#         # เรียงลำดับจากระยะห่างที่น้อยที่สุด (ความหมายใกล้เคียงสุด)
#         base_query += " ORDER BY e.embedding <=> %s::vector LIMIT %s"
#         params.extend([vector_str, limit])

#         # รัน Query
#         cur.execute(base_query, params)
#         results = cur.fetchall()
        
#         return results

#     except Exception as e:
#         print(f"⚠️ Database Search Error: {e}")
#         raise ValueError("เกิดข้อผิดพลาดในการค้นหาข้อมูลในฐานข้อมูล")
    
#     finally:
#         cur.close()