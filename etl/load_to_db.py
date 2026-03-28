"""
Load to DB — Extract skills, สร้าง Semantic Text, embed, แล้ว upsert เข้า PostgreSQL
รองรับ 2 โหมด:
  - CSV Mode (local):  อ่านจาก CSV file
  - DB Mode (cloud):   อ่านจาก DB โดยตรง (สำหรับ GitHub Actions ที่ Phase 1-2 เขียนเข้า DB แล้ว)
"""
import psycopg2
import psycopg2.extras
import pandas as pd
import json
import time
import sys
import os

# Import config และ modules ที่เราเขียนไว้
from etl.config import get_database_url, CSV_FULL_DATA
from etl.extract_skills import extract_skills
from etl.embed_jobs import embed_text


def get_connection():
    """สร้าง connection ไปยัง PostgreSQL (รองรับ DATABASE_URL สำหรับ Supabase)"""
    return psycopg2.connect(get_database_url())


def prepare_semantic_text(title: str, skills_data: dict, raw_jd: str) -> str:
    """
    🛠️ สร้าง Text ที่ 'เข้มข้น' สำหรับการทำ Embedding
    โดยเอา Title และ Skills มาไว้หน้าสุด เพื่อให้ Vector ให้ความสำคัญสูงสุด
    """
    skills_list = skills_data.get("required_skills", [])
    skills_str = ", ".join(skills_list) if skills_list else "Not specified"
    
    exp = skills_data.get("experience_years", "Not specified")
    jtype = skills_data.get("job_type", "Not specified")
    
    # ตัด Raw JD ให้เหลือแค่ 1000 ตัวอักษร เพื่อเป็น Context เสริม (ไม่ให้ Noise เยอะเกินไป)
    # และลบ Newline เยอะๆ ออก
    summary = raw_jd[:1000].replace('\n', ' ').strip()
    
    rich_text = f"""
    Job Title: {title}
    Required Skills: {skills_str}
    Experience Level: {exp}
    Job Type: {jtype}
    
    Job Summary: {summary}
    """.strip()
    
    return rich_text


def get_jobs_from_db(conn) -> pd.DataFrame:
    """
    ดึงงานจาก DB ที่มี JD แล้วแต่ยังไม่ได้ทำ ETL (ยังไม่มี embedding)
    ใช้สำหรับ Cloud mode — Phase 1-2 เขียน jobs+JD เข้า DB แล้ว
    """
    query = """
        SELECT j.id, j.title, j.company, j.location, j.salary, j.link, j.description
        FROM jobs j
        LEFT JOIN job_embeddings e ON j.id = e.job_id
        WHERE j.description IS NOT NULL
          AND j.description NOT IN ('', 'Not Found', 'Error', 'No Link')
          AND e.job_id IS NULL
        ORDER BY j.id
    """
    return pd.read_sql(query, conn)


def update_job_skills(cur, job_id: int, skills_data: dict):
    """Update skills/experience/job_type ของ job ที่มีอยู่แล้วใน DB"""
    cur.execute("""
        UPDATE jobs SET
            skills = %s,
            experience_years = %s,
            job_type = %s,
            is_active = true,
            updated_at = NOW()
        WHERE id = %s
    """, (
        json.dumps(skills_data.get('required_skills', []), ensure_ascii=False),
        skills_data.get('experience_years', 'Not specified'),
        skills_data.get('job_type', 'Not specified'),
        job_id,
    ))



def check_semantic_duplicate(cur, title: str, company: str, location: str):
    """
    เช็คว่ามีงานนี้ใน DB แล้วหรือยัง (Title + Company + Location)
    Returns: (id, link) ถ้าเจอ, None ถ้าไม่เจอ
    """
    cur.execute("""
        SELECT id, link, skills, experience_years, job_type FROM jobs 
        WHERE title = %s AND company = %s AND location = %s
        LIMIT 1
    """, (title, company, location))
    return cur.fetchone()


def upsert_job(cur, job: dict) -> int:
    """
    Insert หรือ update job ใน DB (ใช้ link เป็น unique key)
    เพิ่มการเช็ค Title + Company + Location เพื่อป้องกันงานซ้ำแบบ Semantic
    Returns: job id
    """
    # หมายเหตุ: การเช็ค Semantic Duplicate ย้ายไปทำที่ run_pipeline แล้ว
    # เพื่อประหยัด Resource (ไม่ต้อง Embed ฟรี)
    # แต่ถ้าจะกันเหนียวไว้ตรงนี้อีกชั้นก็ได้ หรือจะเน้น Update ตาม Link เป็นหลัก
    
    # 2. ถ้าไม่ซ้ำ ก็ Insert/Update ตามปกติ (ใช้ Link เป็น Key หลักในการ ON CONFLICT)

    cur.execute("""
        INSERT INTO jobs (title, company, location, salary, link, description, skills, experience_years, job_type, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (link) DO UPDATE SET
            title = EXCLUDED.title,
            company = EXCLUDED.company,
            location = EXCLUDED.location,
            salary = EXCLUDED.salary,
            description = EXCLUDED.description,
            skills = EXCLUDED.skills,
            experience_years = EXCLUDED.experience_years,
            job_type = EXCLUDED.job_type,
            is_active = true,
            updated_at = NOW()
        RETURNING id
    """, (
        job['title'],
        job['company'],
        job['location'],
        job['salary'],
        job['link'],
        job['description'],
        json.dumps(job.get('skills', []), ensure_ascii=False),
        job.get('experience_years', 'Not specified'),
        job.get('job_type', 'Not specified'),
    ))
    return cur.fetchone()[0]


def upsert_embedding(cur, job_id: int, embedding: list, model: str = 'gemini-embedding-001'):
    """Insert หรือ update embedding สำหรับ job"""
    if embedding is None:
        return
    cur.execute("""
        INSERT INTO job_embeddings (job_id, embedding, model)
        VALUES (%s, %s, %s)
        ON CONFLICT (job_id) DO UPDATE SET
            embedding = EXCLUDED.embedding,
            model = EXCLUDED.model,
            created_at = NOW()
    """, (job_id, str(embedding), model))


def run_pipeline(csv_path: str = None, limit: int = None, from_db: bool = False):
    """
    ETL Pipeline หลัก (Updated for Semantic Embedding):
    1. อ่านข้อมูล (CSV หรือ DB)
    2. Extract skills (Groq — llama-3.1-8b-instant)
    3. Construct Rich Text (Title + Skills + Summary)
    4. Embed Rich Text (Gemini Embedding)
    5. Upsert เข้า PostgreSQL

    Auto-detect: ถ้าไม่มี CSV → ใช้ DB mode (สำหรับ cloud)
    """
    csv_path = csv_path or CSV_FULL_DATA

    # Auto-detect: ถ้า force DB mode หรือ CSV ไม่มี → ใช้ DB mode
    if from_db or not os.path.exists(csv_path):
        if not from_db:
            print(f"📂 ไม่พบ CSV ({os.path.basename(csv_path)}) → สลับเป็น DB mode")
        return run_pipeline_from_db(limit=limit)

    print(f"📂 โหลดข้อมูลจาก {os.path.basename(csv_path)}...")
    df = pd.read_csv(csv_path)
    
    # Clean Data เบื้องต้น
    df = df[df['JobDescription'].notna() & ~df['JobDescription'].isin(["Not Found", "Error", "No Link"])]
    df = df.reset_index(drop=True)

    if limit:
        df = df.head(limit)

    print(f"📊 จะประมวลผล {len(df)} งาน\n")

    # Connect DB
    conn = get_connection()
    cur = conn.cursor()
    
    # เช็คของเดิมใน DB เพื่อข้ามงานที่ทำเสร็จแล้ว
    cur.execute("SELECT j.link FROM job_embeddings e JOIN jobs j ON e.job_id = j.id")
    finished_links = set(row[0] for row in cur.fetchall())
    
    print(f"🔍 งานที่ processed เสร็จสมบูรณ์แล้วใน DB: {len(finished_links)} งาน\n")

    success = 0
    errors = 0
    skipped = 0

    for idx, row in df.iterrows():
        title = row['Title']
        link = row['Link']
        jd = row['JobDescription']

        # ถ้ามี Embedding แล้ว ถือว่าจบ ข้ามเลย
        if link in finished_links:
            skipped += 1
            # print(f"⏭️ ข้าม: {title[:30]}...") 
            continue

        print(f"[{idx+1}/{len(df)}] {title[:50]}...")

        # ---------------------------------------------------------
        # STEP 0: Check Semantic Duplicate (Improved Logic)
        # ---------------------------------------------------------
        # เช็ค Title + Company + Location ก่อน
        potential_dup = check_semantic_duplicate(cur, title, row.get('Company', ''), row.get('Location', ''))
        
        # ตัวแปรสำหรับเก็บ skills ที่อาจจะ extract มาแล้ว
        skills_data = None 

        if potential_dup:
            existing_id, existing_link, existing_skills, existing_exp, existing_type = potential_dup
            
            # ถ้าเจอ ให้ลอง Extract Skills ของงานใหม่มาเทียบดูเลย
            # (ยอมเสียเวลา Extract หน่อย เพื่อความชัวร์)
            print(f"   🤔 Found potential duplicate (ID {existing_id}). Checking details...")
            
            try:
                # Extract Skills ของงานใหม่ (ถ้ายังไม่ได้ทำ)
                skills_data = extract_skills(jd)
                
                # เตรียมข้อมูลสำหรับเทียบ (แปลงเป็น string หรือ format เดียวกันให้มากที่สุด)
                new_skills_list = skills_data.get('required_skills', [])
                new_exp = skills_data.get('experience_years', 'Not specified')
                new_type = skills_data.get('job_type', 'Not specified')
                
                # Compare (แบบบ้านๆ)
                # หมายเหตุ: existing_skills ใน DB น่าจะเก็บเป็น list หรือ json
                # เราดึงมาจาก psycopg2 ถ้าเป็น json field มันจะแปลงเป็น list/dict ให้เลย หรือถ้าเป็น text ต้อง json.loads
                # แต่ใน upsert ใส่เป็น json.dumps แสดงว่าเป็น text หรือ jsonb
                
                # ปรับให้มั่นใจว่าเป็น list
                existing_skills_list = []
                if isinstance(existing_skills, str):
                    try:
                        existing_skills_list = json.loads(existing_skills)
                    except:
                        existing_skills_list = []
                elif isinstance(existing_skills, list):
                    existing_skills_list = existing_skills
                
                # เทียบกันเลย
                skills_match = set(new_skills_list) == set(existing_skills_list)
                exp_match = new_exp == existing_exp
                type_match = new_type == existing_type
                
                if skills_match and exp_match and type_match:
                    print(f"   ⚠️  Skipping (Truly Duplicate - Same Skills/Exp/Type): ID {existing_id}")
                    skipped += 1
                    continue
                else:
                    print(f"   ✨ Looks different! Proceeding as new job/version.")
                    # ถ้าต่างกัน ก็ทำต่อ (โดยใช้ skills_data ที่ extract มาแล้ว)
            
            except Exception as e:
                print(f"   ❌ Error checking details: {e}. Proceeding anyway.")
                # ถ้าเช็คไม่ผ่าน ก็ทำต่อแบบปกติไป

        try:
            # ---------------------------------------------------------
            # STEP 1: Extract Skills (ถ้ายังไม่มี)
            # ---------------------------------------------------------
            if not skills_data:
                skills_data = extract_skills(jd)
            
            if skills_data['required_skills']:
                print(f"   🧠 Skills: {skills_data['required_skills'][:5]}...")
            else:
                print(f"   🧠 ไม่พบ skills")

            # ---------------------------------------------------------
            # STEP 2: Construct Semantic Rich Text (หัวใจสำคัญ!)
            # ---------------------------------------------------------
            semantic_text = prepare_semantic_text(title, skills_data, jd)
            print(f"   📝 Semantic Text Len: {len(semantic_text)} chars") # Uncomment ถ้าอยาก debug

            # ---------------------------------------------------------
            # STEP 3: Embed (ใช้ Semantic Text แทน JD ดิบ)
            # ---------------------------------------------------------
            embedding = embed_text(semantic_text)
            
            if embedding:
                print(f"   📐 Embedding: {len(embedding)} dims (Generated from Rich Text)")
            else:
                print(f"   ⚠️ Embedding ล้มเหลว")

            # ---------------------------------------------------------
            # STEP 4: Save to DB
            # ---------------------------------------------------------
            # เตรียมข้อมูลสำหรับตาราง jobs
            job_data = {
                'title': title,
                'company': row.get('Company', ''),
                'location': row.get('Location', ''),
                'salary': row.get('Salary', ''),
                'link': link,
                'description': jd, # เก็บ JD ดิบไว้แสดงผลหน้าเว็บ
                'skills': skills_data.get('required_skills', []),
                'experience_years': skills_data.get('experience_years', 'Not specified'),
                'job_type': skills_data.get('job_type', 'Not specified'),
            }

            # Upsert Table: jobs
            job_id = upsert_job(cur, job_data)

            # Upsert Table: job_embeddings
            if embedding:
                upsert_embedding(cur, job_id, embedding)

            conn.commit()
            success += 1
            print(f"   ✅ บันทึก DB สำเร็จ (id={job_id})")

        except Exception as e:
            conn.rollback()
            errors += 1
            print(f"   ❌ Error: {e}")

    cur.close()
    conn.close()

    print(f"\n{'='*50}")
    print(f"🎉 ETL Pipeline เสร็จสิ้น!")
    print(f"   ✅ Processed & Saved: {success}")
    print(f"   ⏭️ Skipped (Already Done): {skipped}")
    print(f"   ❌ Errors: {errors}")
    print(f"{'='*50}")


def run_pipeline_from_db(limit: int = None):
    """
    ETL Pipeline สำหรับ Cloud: อ่าน jobs จาก DB → Extract Skills → Embed → Update DB
    ใช้เมื่อ Phase 1-2 (scraping) เขียนเข้า DB แล้ว ไม่ต้องอ่านจาก CSV
    """
    print("☁️  Cloud Mode: อ่านข้อมูลจาก DB โดยตรง")

    conn = get_connection()

    # ดึงงานที่มี JD แต่ยังไม่มี embedding
    df = get_jobs_from_db(conn)

    if limit:
        df = df.head(limit)

    print(f"📊 จะประมวลผล {len(df)} งาน (มี JD แต่ยังไม่มี embedding)\n")

    if len(df) == 0:
        print("✅ ไม่มีงานใหม่ที่ต้องประมวลผล!")
        conn.close()
        return

    cur = conn.cursor()
    success = 0
    errors = 0

    for idx, row in df.iterrows():
        title = row['title']
        job_id = row['id']
        jd = row['description']

        print(f"[{idx+1}/{len(df)}] {title[:50]}...")

        try:
            # STEP 1: Extract Skills
            skills_data = extract_skills(jd)

            if skills_data['required_skills']:
                print(f"   🧠 Skills: {skills_data['required_skills'][:5]}...")
            else:
                print(f"   🧠 ไม่พบ skills")

            # STEP 2: Construct Semantic Rich Text
            semantic_text = prepare_semantic_text(title, skills_data, jd)
            print(f"   📝 Semantic Text Len: {len(semantic_text)} chars")

            # STEP 3: Embed
            embedding = embed_text(semantic_text)

            if embedding:
                print(f"   📐 Embedding: {len(embedding)} dims")
            else:
                print(f"   ⚠️ Embedding ล้มเหลว")

            # STEP 4: Update skills + Upsert embedding
            update_job_skills(cur, job_id, skills_data)

            if embedding:
                upsert_embedding(cur, job_id, embedding)

            conn.commit()
            success += 1
            print(f"   ✅ บันทึก DB สำเร็จ (id={job_id})")

        except Exception as e:
            conn.rollback()
            errors += 1
            print(f"   ❌ Error: {e}")

    cur.close()
    conn.close()

    print(f"\n{'='*50}")
    print(f"🎉 ETL Pipeline (Cloud Mode) เสร็จสิ้น!")
    print(f"   ✅ Processed & Saved: {success}")
    print(f"   ❌ Errors: {errors}")
    print(f"{'='*50}")


if __name__ == '__main__':
    limit = None
    from_db = False

    args = sys.argv[1:]
    if '--from-db' in args:
        from_db = True
        args.remove('--from-db')
    if '--limit' in args:
        limit_idx = args.index('--limit')
        limit = int(args[limit_idx + 1])

    run_pipeline(limit=limit, from_db=from_db)