import os
import sys
from scraper_db import get_connection

def main():
    print("🔌 กำลังเชื่อมต่อฐานข้อมูล...")
    conn = get_connection()
    if not conn:
        print("❌ เชื่อมต่อเดต้าเบสไม่สำเร็จ")
        sys.exit(1)
        
    cur = conn.cursor()
    
    # 1. Check total jobs
    cur.execute("SELECT COUNT(*) FROM jobs;")
    total_jobs = cur.fetchone()[0]
    
    # 2. Check jobs by is_active
    cur.execute("SELECT is_active, COUNT(*) FROM jobs GROUP BY is_active;")
    active_stats = cur.fetchall()
    
    # 3. Check total embeddings
    cur.execute("SELECT COUNT(*) FROM job_embeddings;")
    total_embeds = cur.fetchone()[0]
    
    # 4. Check active jobs WITH embeddings
    query_active_with_embed = """
        SELECT COUNT(j.id) 
        FROM jobs j
        JOIN job_embeddings e ON j.id = e.job_id
        WHERE j.is_active = true;
    """
    cur.execute(query_active_with_embed)
    active_with_embeds = cur.fetchone()[0]

    # Print Report
    print(f"\n{'='*50}")
    print(f"📊 รายงานสถิติข้อมูลใน Database (JobMatcher)")
    print(f"{'='*50}")
    
    print(f"\n🏢 [ตาราง jobs]")
    print(f"   จำนวนงานสะสมทั้งหมด: {total_jobs:,} แถว")
    
    for stat in active_stats:
        status_text = "🟢 เปิดรับอยู่ (Active)" if stat[0] else "🔴 ติดสถานะเก่า/ตกรุ่น (Inactive)"
        print(f"   - {status_text}: {stat[1]:,} แถว")
    
    print(f"\n🧠 [ตาราง job_embeddings]")
    print(f"   จำนวนเวกเตอร์ทั้งหมด: {total_embeds:,} แถว")
    
    missing_embeds = total_jobs - total_embeds
    if missing_embeds > 0:
        print(f"   ⚠️ ขาดอีก {missing_embeds:,} งานที่ยังไม่ได้จำลองเวกเตอร์ (รอรัน ETL)")
    else:
        print(f"   ✅ ข้อมูลเวกเตอร์ถูกฝังครบ 100% ของจำนวนงานทั้งหมด")
        
    print(f"\n🚀 [สรุปความพร้อมสำหรับการค้นหา (RAG)]")
    print(f"   งานที่พร้อมถูกดึงโชว์ให้หน้าเว็บ (Active + มีเวกเตอร์): {active_with_embeds:,} งาน")
    print(f"{'='*50}\n")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
