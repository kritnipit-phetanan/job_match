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


@router.get("/salary-trends")
def get_salary_trends(
    limit: int = 20,
    min_jobs: int = 3,
    db_conn=Depends(get_db_connection)
):
    """
    คำนวณเงินเดือนเฉลี่ย (min/max/avg) ต่อ Skill จากข้อมูลงานที่มี salary เป็นรูปแบบ ฿
    ใช้เพื่อแสดง Salary Trends Chart
    """
    cur = db_conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            WITH parsed AS (
                SELECT
                    skill,
                    CAST(REGEXP_REPLACE(SPLIT_PART(salary, '–', 1), '[^0-9]', '', 'g') AS INTEGER) AS sal_min,
                    CAST(REGEXP_REPLACE(SPLIT_PART(salary, '–', 2), '[^0-9]', '', 'g') AS INTEGER) AS sal_max
                FROM jobs, jsonb_array_elements_text(skills) AS skill
                WHERE salary LIKE '%%฿%%' AND salary LIKE '%%–%%'
            )
            SELECT
                skill AS name,
                COUNT(*) AS job_count,
                ROUND(AVG(sal_min)) AS avg_min,
                ROUND(AVG(sal_max)) AS avg_max,
                ROUND(AVG((sal_min + sal_max) / 2)) AS avg_salary
            FROM parsed
            GROUP BY skill
            HAVING COUNT(*) >= %s
            ORDER BY avg_salary DESC
            LIMIT %s
        """, [min_jobs, limit])

        skills = cur.fetchall()

        # จำนวนงานที่มี salary ใช้งานได้
        cur.execute("SELECT COUNT(*) AS total FROM jobs WHERE salary LIKE '%%฿%%' AND salary LIKE '%%–%%'")
        total_with_salary = cur.fetchone()["total"]

        return {
            "status": "success",
            "total_jobs_with_salary": total_with_salary,
            "skills": [
                {
                    "name": row["name"],
                    "job_count": row["job_count"],
                    "avg_min": int(row["avg_min"]),
                    "avg_max": int(row["avg_max"]),
                    "avg_salary": int(row["avg_salary"]),
                }
                for row in skills
            ]
        }

    except Exception as e:
        print(f"🔥 Error ใน /salary-trends: {e}")
        return {"status": "error", "total_jobs_with_salary": 0, "skills": []}
    finally:
        cur.close()
