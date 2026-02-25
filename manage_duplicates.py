"""
Manage Duplicates — ตรวจสอบและลบงานซ้ำ
รองรับ 2 โหมด:
  - CSV Mode (default): ตรวจสอบจากไฟล์ CSV
  - DB Mode (--db):     ตรวจสอบจาก Supabase โดยตรง

Usage:
  python manage_duplicates.py check                  # เช็คซ้ำจาก CSV
  python manage_duplicates.py check --db              # เช็คซ้ำจาก DB
  python manage_duplicates.py remove                  # ลบซ้ำจาก CSV
  python manage_duplicates.py remove --db             # ลบซ้ำจาก DB
  python manage_duplicates.py remove --db --dry-run   # ดูก่อนว่าจะลบอะไร (ไม่ลบจริง)
"""
import csv
import os
import shutil
import argparse
from collections import defaultdict


def normalize(text):
    return text.strip().lower() if text else ''


# ============================================================
# CSV Mode
# ============================================================
def check_duplicates(files):
    print("Checking for duplicates where (Title+Company+Location) match but Links differ...")
    
    grouped_jobs = defaultdict(list)

    for filename in files:
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = normalize(row.get('Title', ''))
                    company = normalize(row.get('Company', ''))
                    location = normalize(row.get('Location', ''))
                    link = row.get('Link', '').strip()
                    
                    key = (title, company, location)
                    grouped_jobs[key].append({
                        'Title': row.get('Title', ''),
                        'Company': row.get('Company', ''),
                        'Location': row.get('Location', ''),
                        'Link': link,
                        'Source': filename
                    })
        except FileNotFoundError:
            print(f"Error: File {filename} not found.")
            return

    duplicates_found = False
    
    for key, jobs in grouped_jobs.items():
        unique_links = set(job['Link'] for job in jobs)
        
        if len(unique_links) > 1:
            duplicates_found = True
            print(f"\n--- Duplicate Job Found ---")
            print(f"Title: {jobs[0]['Title']}")
            print(f"Company: {jobs[0]['Company']}")
            print(f"Location: {jobs[0]['Location']}")
            print(f"Different Links ({len(unique_links)}):")
            for job in jobs:
                print(f"  - Link: {job['Link']} (from {job['Source']})")

    if not duplicates_found:
        print("\nNo duplicates with different links found based on Title+Company+Location.")


def remove_duplicates(files):
    for filename in files:
        print(f"Processing {filename}...")
        temp_filename = filename + '.tmp'
        
        unique_jobs = set()
        kept_count = 0
        removed_count = 0
        
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f_in, \
                 open(temp_filename, 'w', encoding='utf-8-sig', newline='') as f_out:
                
                reader = csv.DictReader(f_in)
                fieldnames = reader.fieldnames
                writer = csv.DictWriter(f_out, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in reader:
                    title = normalize(row.get('Title', ''))
                    company = normalize(row.get('Company', ''))
                    location = normalize(row.get('Location', ''))
                    
                    key = (title, company, location)
                    
                    if key in unique_jobs:
                        removed_count += 1
                    else:
                        unique_jobs.add(key)
                        writer.writerow(row)
                        kept_count += 1
                        
            shutil.move(temp_filename, filename)
            print(f"  Finished. Kept: {kept_count}, Removed: {removed_count}")
            
        except FileNotFoundError:
            print(f"Error: File {filename} not found.")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            if os.path.exists(temp_filename):
                os.remove(temp_filename)


# ============================================================
# DB Mode (Supabase)
# ============================================================
def get_db_connection():
    """สร้าง connection ไปยัง Supabase"""
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
    database_url = os.getenv('DATABASE_URL', '')
    if not database_url:
        raise ValueError("❌ DATABASE_URL not set in .env")
    return psycopg2.connect(database_url)


def check_duplicates_db():
    """ตรวจสอบงานซ้ำใน DB (Title+Company+Location เหมือนกัน แต่ Link ต่างกัน)"""
    print("🔍 ตรวจสอบงานซ้ำใน DB (Supabase)...\n")

    conn = get_db_connection()
    cur = conn.cursor()

    # หากลุ่มที่มี Title+Company+Location เหมือนกัน แต่มีหลาย row
    cur.execute("""
        SELECT LOWER(TRIM(title)), LOWER(TRIM(company)), LOWER(TRIM(location)), 
               COUNT(*) as cnt
        FROM jobs
        GROUP BY LOWER(TRIM(title)), LOWER(TRIM(company)), LOWER(TRIM(location))
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
    """)
    dup_groups = cur.fetchall()

    if not dup_groups:
        print("✅ ไม่พบงานซ้ำใน DB!")
        cur.close()
        conn.close()
        return

    total_dups = 0
    for title, company, location, cnt in dup_groups:
        # ดึงรายละเอียดของแต่ละกลุ่ม
        cur.execute("""
            SELECT id, title, company, location, link, 
                   CASE WHEN description IS NOT NULL AND description != '' THEN 'Yes' ELSE 'No' END as has_jd,
                   created_at
            FROM jobs
            WHERE LOWER(TRIM(title)) = %s 
              AND LOWER(TRIM(company)) = %s 
              AND LOWER(TRIM(location)) = %s
            ORDER BY id
        """, (title, company, location))
        rows = cur.fetchall()

        print(f"--- งานซ้ำ ({cnt} รายการ) ---")
        print(f"  Title:    {rows[0][1]}")
        print(f"  Company:  {rows[0][2]}")
        print(f"  Location: {rows[0][3]}")
        for row in rows:
            print(f"  • ID: {row[0]} | Link: {row[4][:60]}... | JD: {row[5]} | Created: {row[6]}")
        print()
        total_dups += cnt - 1  # จำนวนที่ซ้ำ (ลบตัวแรกออก)

    print(f"📊 สรุป: พบ {len(dup_groups)} กลุ่มงานซ้ำ (รวม {total_dups} แถวที่สามารถลบได้)")
    cur.close()
    conn.close()


def remove_duplicates_db(dry_run=False):
    """
    ลบงานซ้ำใน DB (เก็บแถวที่เก่าที่สุดไว้ = id น้อยสุด)
    ลบ job_embeddings ที่เกี่ยวข้องด้วย
    """
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"🗑️ ลบงานซ้ำใน DB ({mode})...\n")

    conn = get_db_connection()
    cur = conn.cursor()

    # หา id ที่ต้องลบ (เก็บ id ที่ใหม่ที่สุดของแต่ละกลุ่มไว้ ลบตัวเก่าออก)
    cur.execute("""
        SELECT id FROM jobs
        WHERE id NOT IN (
            SELECT MAX(id) 
            FROM jobs
            GROUP BY LOWER(TRIM(title)), LOWER(TRIM(company)), LOWER(TRIM(location))
        )
        AND id IN (
            SELECT id FROM jobs j2
            WHERE (
                SELECT COUNT(*) FROM jobs j3
                WHERE LOWER(TRIM(j3.title)) = LOWER(TRIM(j2.title))
                  AND LOWER(TRIM(j3.company)) = LOWER(TRIM(j2.company))
                  AND LOWER(TRIM(j3.location)) = LOWER(TRIM(j2.location))
            ) > 1
        )
        ORDER BY id
    """)
    ids_to_delete = [row[0] for row in cur.fetchall()]

    if not ids_to_delete:
        print("✅ ไม่มีงานซ้ำที่ต้องลบ!")
        cur.close()
        conn.close()
        return

    print(f"📋 พบ {len(ids_to_delete)} แถวที่ซ้ำ (จะลบ IDs: {ids_to_delete[:20]}{'...' if len(ids_to_delete) > 20 else ''})")

    if dry_run:
        # แสดงรายละเอียดแถวที่จะลบ
        for job_id in ids_to_delete[:10]:
            cur.execute("SELECT id, title, company, link FROM jobs WHERE id = %s", (job_id,))
            row = cur.fetchone()
            if row:
                print(f"  🗑️ ID {row[0]}: {row[1][:40]} | {row[2]} | {row[3][:50]}...")
        if len(ids_to_delete) > 10:
            print(f"  ... และอีก {len(ids_to_delete) - 10} แถว")
        print(f"\n⚠️ DRY RUN — ไม่ได้ลบจริง ถ้าต้องการลบจริง ให้รันโดยไม่ใส่ --dry-run")
    else:
        # ลบ embeddings ก่อน (foreign key)
        cur.execute(
            "DELETE FROM job_embeddings WHERE job_id = ANY(%s)",
            (ids_to_delete,)
        )
        embed_deleted = cur.rowcount
        
        # ลบ jobs
        cur.execute(
            "DELETE FROM jobs WHERE id = ANY(%s)",
            (ids_to_delete,)
        )
        jobs_deleted = cur.rowcount

        conn.commit()
        print(f"\n✅ ลบสำเร็จ!")
        print(f"   🗑️ Jobs deleted: {jobs_deleted}")
        print(f"   🗑️ Embeddings deleted: {embed_deleted}")

    cur.close()
    conn.close()


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Manage duplicate jobs (CSV or DB).")
    parser.add_argument('action', choices=['check', 'remove'], help="Action: 'check' or 'remove'")
    parser.add_argument('--db', action='store_true', help="ใช้ DB (Supabase) แทน CSV")
    parser.add_argument('--dry-run', action='store_true', help="แสดงผลอย่างเดียว ไม่ลบจริง (ใช้กับ remove --db)")
    parser.add_argument('--files', nargs='+', default=['jobsdb_result_all.csv', 'jobsdb_full_data.csv'], help="CSV files to process")
    
    args = parser.parse_args()
    
    if args.action == 'check':
        if args.db:
            check_duplicates_db()
        else:
            check_duplicates(args.files)
    elif args.action == 'remove':
        if args.db:
            remove_duplicates_db(dry_run=args.dry_run)
        else:
            remove_duplicates(args.files)


if __name__ == "__main__":
    main()
