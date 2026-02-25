"""
Cloud Scrape Details — Phase 2: เข้าแต่ละ Link เพื่อดึง JD แล้ว update เข้า Supabase
รัน: python cloud_scrape_details.py
Options: HEADLESS=false python cloud_scrape_details.py  (เปิด browser ให้ดูได้)
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import random

from scraper_db import (
    get_connection, get_pending_jobs, update_description,
    get_browser_config, load_cookies, save_cookies,
    human_like_scroll, human_like_mouse, smart_delay,
    solve_cloudflare_turnstile,
    HEADLESS,
)

# Flag สำหรับลิงก์เสีย → ข้ามเมื่อรันใหม่
BROKEN_LINK_FLAG = "Not Found"


# ============================================================
# Main Pipeline
# ============================================================
def run():
    # ---------------------------------------------------------
    # 1. ดึงรายการ jobs ที่ยังไม่มี JD จาก Supabase
    # ---------------------------------------------------------
    print("📡 เชื่อมต่อ Supabase...")
    conn = get_connection()
    pending_jobs = get_pending_jobs(conn)

    print(f"\n📊 สรุป:")
    print(f"   🆕 งานที่ต้อง scrape JD: {len(pending_jobs)} งาน\n")

    if len(pending_jobs) == 0:
        print("✅ ไม่มีงานใหม่ ทุกงานมี JD หมดแล้ว!")
        conn.close()
        return

    # ---------------------------------------------------------
    # 2. เริ่ม Scrape JD
    # ---------------------------------------------------------
    success_count = 0
    flagged_count = 0
    error_count = 0

    with sync_playwright() as p:
        print(f"🚀 เริ่มต้นระบบ... (headless={HEADLESS})")
        browser_config = get_browser_config()
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent=browser_config["user_agent"],
            extra_http_headers=browser_config["extra_http_headers"],
            viewport={'width': 1280, 'height': 800},
            locale='th-TH'
        )

        # โหลด cookies
        load_cookies(context)

        page = context.new_page()
        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        # Warm-up
        print("🚀 Warm-up: เข้าหน้าแรกก่อน...")
        try:
            page.goto("https://th.jobsdb.com/", timeout=60000)
            human_like_mouse(page)
            time.sleep(random.uniform(2, 4))
            solve_cloudflare_turnstile(page)
        except Exception as e:
            print(f"⚠️ Warm-up ช้า: {e}")

        print(f"🚀 เริ่มเจาะ JD {len(pending_jobs)} งาน...\n")

        for index, (job_id, link, title) in enumerate(pending_jobs):
            print(f"[{index+1}/{len(pending_jobs)}] {title[:50]}...")

            try:
                page.goto(link, timeout=30000)
                solve_cloudflare_turnstile(page)

                # ขยับเมาส์ + scroll เหมือนมนุษย์อ่าน JD จริงๆ
                time.sleep(random.uniform(1, 2))
                human_like_mouse(page)
                human_like_scroll(page)

                # หา Job Description (ลองหลาย selector)
                jd_text = None
                jd_selectors = [
                    '[data-automation="jobDescription"]',
                    'div[data-automation="job-details"]',
                    '[data-automation="jobAdDetails"]',
                    'div[class*="jobDescription"]',
                    'div[class*="job-description"]',
                ]

                for sel in jd_selectors:
                    if page.locator(sel).count() > 0:
                        jd_text = page.locator(sel).first.inner_text().strip()
                        if jd_text:
                            break

                if jd_text:
                    update_description(conn, link, jd_text)
                    success_count += 1
                    print(f"   ✅ ดึง JD สำเร็จ! ({len(jd_text)} chars) → DB updated")
                else:
                    update_description(conn, link, BROKEN_LINK_FLAG)
                    flagged_count += 1
                    print(f"   ⚠️ หา JD ไม่เจอ → flagged '{BROKEN_LINK_FLAG}'")

            except Exception as e:
                update_description(conn, link, "Error")
                error_count += 1
                print(f"   ❌ Error: {e}")

            # หน่วงเวลาอัจฉริยะ
            smart_delay(index, len(pending_jobs))

        # บันทึก cookies สุดท้าย
        save_cookies(context)
        browser.close()

    conn.close()

    # ---------------------------------------------------------
    # สรุปผล
    # ---------------------------------------------------------
    print(f"\n{'='*50}")
    print(f"🎉 Phase 2 เสร็จสิ้น!")
    print(f"   ✅ ดึง JD ได้: {success_count}/{len(pending_jobs)}")
    if flagged_count:
        print(f"   🚩 ลิงก์เสีย: {flagged_count} (จะข้ามในรอบถัดไป)")
    if error_count:
        print(f"   ❌ Error: {error_count} (จะ retry รอบถัดไป)")
    print(f"{'='*50}")


if __name__ == '__main__':
    run()
