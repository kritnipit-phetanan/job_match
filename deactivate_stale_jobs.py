"""
Deactivate Stale Jobs — ปิดงานที่ไม่ได้อัปเดตเกิน 30 วัน
งานจะถูก set is_active = false แต่ไม่ถูกลบออกจาก DB

Usage:
  python deactivate_stale_jobs.py              # deactivate จริง
  python deactivate_stale_jobs.py --dry-run    # ดูก่อน ไม่แก้จริง
  python deactivate_stale_jobs.py --days 60    # เปลี่ยนเป็น 60 วัน
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


def deactivate_stale(conn, days=30, dry_run=False):
    """Deactivate งานที่ updated_at เกินจำนวนวันที่กำหนด"""
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"🔍 ตรวจสอบงานที่ไม่ได้อัปเดตเกิน {days} วัน ({mode})...\n")

    cur = conn.cursor()

    # ดูจำนวนงานที่จะถูก deactivate
    cur.execute("""
        SELECT COUNT(*) FROM jobs
        WHERE created_at < NOW() - INTERVAL '%s days'
          AND is_active = true
    """, [days])
    stale_count = cur.fetchone()[0]

    if stale_count == 0:
        print("✅ ไม่มีงานที่ต้อง deactivate")
        cur.close()
        return 0

    print(f"📋 พบ {stale_count} งานที่ updated_at เกิน {days} วัน")

    if dry_run:
        # แสดงตัวอย่างงานที่จะถูก deactivate
        cur.execute("""
            SELECT id, title, company, updated_at
            FROM jobs
            WHERE created_at < NOW() - INTERVAL '%s days'
              AND is_active = true
            ORDER BY updated_at ASC
            LIMIT 10
        """, [days])
        samples = cur.fetchall()
        for row in samples:
            print(f"  • ID {row[0]}: {row[1][:50]} | {row[2]} | updated: {row[3]}")
        if stale_count > 10:
            print(f"  ... และอีก {stale_count - 10} งาน")
        print(f"\n⚠️ DRY RUN — ไม่ได้แก้จริง รัน python deactivate_stale_jobs.py เพื่อ deactivate จริง")
    else:
        cur.execute("""
            UPDATE jobs SET is_active = false
            WHERE created_at < NOW() - INTERVAL '%s days'
              AND is_active = true
        """, [days])
        conn.commit()
        print(f"✅ Deactivated {stale_count} งานสำเร็จ!")

    cur.close()
    return stale_count


def main():
    parser = argparse.ArgumentParser(description="Deactivate stale jobs (30+ days since last update)")
    parser.add_argument('--dry-run', action='store_true', help="ดูก่อน ไม่แก้จริง")
    parser.add_argument('--days', type=int, default=30, help="จำนวนวันที่ถือว่าเก่า (default: 30)")
    args = parser.parse_args()

    conn = get_connection()
    deactivate_stale(conn, days=args.days, dry_run=args.dry_run)
    conn.close()


if __name__ == '__main__':
    main()
