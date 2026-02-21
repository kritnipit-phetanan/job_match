from fastapi import APIRouter, Depends
from psycopg2.extras import RealDictCursor
from app.core.database import get_db_connection

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/hot-skills")
def get_hot_skills(
    limit: int = 30,
    db_conn=Depends(get_db_connection)
):
    """
    นับจำนวน Skill ที่ปรากฏบ่อยที่สุดจากงานทั้งหมดในฐานข้อมูล
    ใช้เพื่อแสดง Market Demand Heatmap
    """
    cur = db_conn.cursor(cursor_factory=RealDictCursor)
    try:
        # นับจำนวนงานทั้งหมด
        cur.execute("SELECT COUNT(*) AS total FROM jobs WHERE skills IS NOT NULL")
        total_jobs = cur.fetchone()["total"]

        # Unnest JSONB array → นับความถี่ของแต่ละ Skill
        cur.execute("""
            SELECT 
                skill,
                COUNT(*) AS count
            FROM jobs, jsonb_array_elements_text(skills) AS skill
            GROUP BY skill
            ORDER BY count DESC
            LIMIT %s
        """, [limit])

        skills = cur.fetchall()

        return {
            "status": "success",
            "total_jobs": total_jobs,
            "skills": [{"name": row["skill"], "count": row["count"]} for row in skills]
        }

    except Exception as e:
        print(f"🔥 Error ใน /hot-skills: {e}")
        return {"status": "error", "total_jobs": 0, "skills": []}
    finally:
        cur.close()
