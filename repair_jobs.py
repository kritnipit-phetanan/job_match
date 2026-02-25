"""
Repair Jobs — แก้ไขงานที่มีปัญหาใน DB
1. รีเซ็ต description ของงานที่เป็น 'Not Found' → ให้ Phase 2 scrape ใหม่
2. ลบ embedding ของงานที่ skills=[] → ให้ ETL extract + embed ใหม่

Usage:
  python repair_jobs.py check          # ดูว่ามีงานไหนต้องซ่อมบ้าง
  python repair_jobs.py fix            # ซ่อมจริง
  python repair_jobs.py fix --dry-run  # ดูก่อน ไม่ซ่อมจริง
"""
import os
import argparse
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))


def get_connection():
    url = os.getenv('DATABASE_URL', '')
    if not url:
        raise ValueError("❌ DATABASE_URL not set")
    return psycopg2.connect(url)


def check(conn):
    """แสดงงานที่มีปัญหา"""
    cur = conn.cursor()

    # 1. งานที่ JD เป็น 'Not Found' หรือ 'No Link'
    cur.execute("""
        SELECT id, title, company, link, description
        FROM jobs
        WHERE description IN ('Not Found', 'No Link')
        ORDER BY id
    """)
    bad_jd = cur.fetchall()

    print(f"\n📋 งานที่ JD = 'Not Found' หรือ 'No Link': {len(bad_jd)} งาน")
    for row in bad_jd:
        print(f"  • ID {row[0]}: {row[1][:40]} | {row[2]} | JD='{row[4]}'")

    # 2. งานที่ skills = [] (empty array)
    cur.execute("""
        SELECT j.id, j.title, j.company, j.skills,
               CASE WHEN e.job_id IS NOT NULL THEN 'Yes' ELSE 'No' END as has_embed
        FROM jobs j
        LEFT JOIN job_embeddings e ON j.id = e.job_id
        WHERE j.skills::text = '[]'
           OR j.skills IS NULL
        ORDER BY j.id
    """)
    empty_skills = cur.fetchall()

    print(f"\n📋 งานที่ skills = [] หรือ NULL: {len(empty_skills)} งาน")
    for row in empty_skills[:15]:
        print(f"  • ID {row[0]}: {row[1][:40]} | {row[2]} | embed={row[4]}")
    if len(empty_skills) > 15:
        print(f"  ... และอีก {len(empty_skills) - 15} งาน")

    # 3. งานที่มี JD แต่ไม่มี embedding (ยังไม่ผ่าน ETL)
    cur.execute("""
        SELECT COUNT(*) FROM jobs j
        LEFT JOIN job_embeddings e ON j.id = e.job_id
        WHERE j.description IS NOT NULL
          AND j.description NOT IN ('', 'Not Found', 'Error', 'No Link')
          AND e.job_id IS NULL
    """)
    pending_etl = cur.fetchone()[0]
    print(f"\n📋 งานที่มี JD แต่ยังไม่มี embedding (รอ ETL): {pending_etl} งาน")

    cur.close()

    print(f"\n{'='*50}")
    total_fixable = len(bad_jd) + len(empty_skills)
    if total_fixable > 0:
        print(f"🔧 รวมงานที่ต้องซ่อม: {total_fixable}")
        print(f"   → รัน: python repair_jobs.py fix")
    else:
        print("✅ ไม่มีงานที่ต้องซ่อม!")


def fix(conn, dry_run=False):
    """ซ่อมงานที่มีปัญหา"""
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"🔧 ซ่อมงานใน DB ({mode})...\n")

    cur = conn.cursor()

    # 1. รีเซ็ต JD ที่เป็น 'Not Found' / 'No Link' → NULL
    #    เพื่อให้ Phase 2 (cloud_scrape_details) หยิบไปทำใหม่
    cur.execute("""
        SELECT id FROM jobs WHERE description IN ('Not Found', 'No Link')
    """)
    bad_jd_ids = [row[0] for row in cur.fetchall()]

    if bad_jd_ids:
        print(f"📝 รีเซ็ต JD ของ {len(bad_jd_ids)} งาน (IDs: {bad_jd_ids})")
        if not dry_run:
            # ลบ embedding ของงานเหล่านี้ก่อน (ถ้ามี)
            cur.execute("DELETE FROM job_embeddings WHERE job_id = ANY(%s)", (bad_jd_ids,))
            # รีเซ็ต description เป็น NULL
            cur.execute("UPDATE jobs SET description = NULL WHERE id = ANY(%s)", (bad_jd_ids,))
            print(f"   ✅ รีเซ็ตแล้ว → Phase 2 จะ scrape ใหม่ในรอบถัดไป")
    else:
        print("📝 ไม่มีงานที่ JD เสีย")

    # 2. ลบ embedding ของงานที่ skills = [] เพื่อให้ ETL ทำใหม่
    cur.execute("""
        SELECT j.id FROM jobs j
        JOIN job_embeddings e ON j.id = e.job_id
        WHERE j.skills::text = '[]'
           OR j.skills IS NULL
    """)
    empty_skills_ids = [row[0] for row in cur.fetchall()]

    if empty_skills_ids:
        print(f"🧠 ลบ embedding ของ {len(empty_skills_ids)} งานที่ skills=[] (IDs: {empty_skills_ids[:20]}{'...' if len(empty_skills_ids) > 20 else ''})")
        if not dry_run:
            cur.execute("DELETE FROM job_embeddings WHERE job_id = ANY(%s)", (empty_skills_ids,))
            # รีเซ็ต skills ด้วย
            cur.execute("UPDATE jobs SET skills = NULL WHERE id = ANY(%s)", (empty_skills_ids,))
            print(f"   ✅ ลบ embedding แล้ว → ETL จะ extract skills + embed ใหม่ในรอบถัดไป")
    else:
        print("🧠 ไม่มีงานที่ skills ว่าง")

    if not dry_run:
        conn.commit()
        total = len(bad_jd_ids) + len(empty_skills_ids)
        print(f"\n✅ ซ่อมเสร็จ! ({total} งาน)")
        print(f"   ขั้นตอนถัดไป:")
        if bad_jd_ids:
            print(f"   1. รัน Phase 2: python cloud_scrape_details.py")
        print(f"   2. รัน ETL:     python -m etl.load_to_db --from-db")
    else:
        print(f"\n⚠️ DRY RUN — ไม่ได้แก้จริง รัน python repair_jobs.py fix เพื่อแก้จริง")

    cur.close()


def main():
    parser = argparse.ArgumentParser(description="Repair problematic jobs in DB")
    parser.add_argument('action', choices=['check', 'fix'], help="'check' or 'fix'")
    parser.add_argument('--dry-run', action='store_true', help="ดูก่อน ไม่แก้จริง")
    args = parser.parse_args()

    conn = get_connection()
    if args.action == 'check':
        check(conn)
    elif args.action == 'fix':
        fix(conn, dry_run=args.dry_run)
    conn.close()


if __name__ == '__main__':
    main()
