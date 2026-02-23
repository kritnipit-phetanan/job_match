"""
Cloud Scrape Jobs — Phase 1: ดึง Job Listing จากหน้า Search แล้ว upsert เข้า Supabase
รัน: python cloud_scrape_jobs.py
Options: HEADLESS=false python cloud_scrape_jobs.py  (เปิด browser ให้ดูได้)
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import random

from scraper_db import (
    get_connection, get_existing_links, upsert_job,
    get_browser_config, load_cookies, save_cookies,
    human_like_scroll, human_like_mouse, normalize_link, make_fingerprint,
    HEADLESS,
)


# ============================================================
# Job Card Helpers
# ============================================================
def find_job_cards(page):
    """ลองหา job cards ด้วยหลาย selectors (เผื่อ JobsDB เปลี่ยน)"""
    selectors = [
        ('[data-automation="jobListing"]',     "data-automation=jobListing"),
        ('div[data-search-sol-meta]',          "data-search-sol-meta"),
        ('article[data-card-type="JobCard"]',  "article JobCard"),
        ('article[data-job-id]',               "article data-job-id"),
        ('div[data-job-id]',                   "div data-job-id"),
        ('article',                            "article (generic)"),
    ]
    for selector, name in selectors:
        cards = page.locator(selector).all()
        if len(cards) > 0:
            return cards, name
    return [], "none"


def extract_job_data(card) -> dict:
    """ดึงข้อมูลจาก job card 1 ใบ"""
    # Title
    title = "N/A"
    for sel in ['[data-automation="jobTitle"]', 'a[data-automation="jobTitle"]', 'h3 a', 'h3']:
        if card.locator(sel).count() > 0:
            title = card.locator(sel).first.inner_text().strip()
            break

    # Company
    company = "N/A"
    for sel in ['[data-automation="jobCompany"]', 'a[data-automation="jobCompany"]', 'span[data-automation="jobCompany"]']:
        if card.locator(sel).count() > 0:
            company = card.locator(sel).first.inner_text().strip()
            break

    # Location
    location = "N/A"
    for sel in ['[data-automation="jobLocation"]', 'a[data-automation="jobLocation"]', 'span[data-automation="jobLocation"]']:
        if card.locator(sel).count() > 0:
            location = card.locator(sel).first.inner_text().strip()
            break

    # Salary
    salary = "N/A"
    for sel in ['[data-automation="jobSalary"]', 'span[data-automation="jobSalary"]']:
        if card.locator(sel).count() > 0:
            salary = card.locator(sel).first.inner_text().strip()
            break

    # Link (normalize เพื่อ dedup)
    link = "N/A"
    if card.locator('a').count() > 0:
        href = card.locator('a').first.get_attribute('href')
        if href:
            if not href.startswith("http"):
                link = "https://th.jobsdb.com" + href
            else:
                link = href
            link = normalize_link(link)

    return {
        "Title": title,
        "Company": company,
        "Location": location,
        "Salary": salary,
        "Link": link,
    }


def smart_wait_for_jobs(page, max_retries=30) -> bool:
    """วนลูปรอจนกว่าจะเจอ job cards"""
    for i in range(max_retries):
        cards, method = find_job_cards(page)
        if len(cards) > 0:
            print(f"✅ เจอ Job Listing แล้ว! ({method}, {len(cards)} cards)")
            return True
        page.mouse.wheel(0, 300)
        print(f"   ...รอ ({i+1}/{max_retries}) - ยังไม่เจอ selector")
        time.sleep(2)
    return False


# ============================================================
# Main Pipeline
# ============================================================
def run():
    keyword = "engineer"
    max_pages = 5
    formatted_keyword = keyword.replace(" ", "-").lower()

    home_url = "https://th.jobsdb.com/"
    search_url = f'https://th.jobsdb.com/{formatted_keyword}-jobs'

    # ---------------------------------------------------------
    # 1. โหลด existing links จาก Supabase (dedup)
    # ---------------------------------------------------------
    print("📡 เชื่อมต่อ Supabase...")
    conn = get_connection()
    existing_links = get_existing_links(conn)
    existing_fingerprints = set()
    print(f"📋 งานที่มีอยู่แล้วใน DB: {len(existing_links)} งาน")

    new_count = 0
    skipped_total = 0

    # ---------------------------------------------------------
    # 2. เปิด Browser
    # ---------------------------------------------------------
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

        # Apply Stealth
        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        # ---------------------------------------------------------
        # STEP 1: Warm-up (เข้าหน้าแรก)
        # ---------------------------------------------------------
        print(f"1️⃣ Warm-up: เข้าหน้าแรก {home_url}")
        try:
            page.goto(home_url, timeout=60000)
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            print(f"⚠️ เข้าหน้าแรกช้า: {e}")

        # ขยับเมาส์หลอกๆ
        human_like_mouse(page)
        save_cookies(context)

        # ---------------------------------------------------------
        # STEP 2: ไปหน้าค้นหา
        # ---------------------------------------------------------
        print(f"2️⃣ ไปหน้าค้นหา: {search_url}")
        try:
            page.goto(search_url, timeout=60000)
        except Exception as e:
            print(f"⚠️ เข้าหน้าค้นหาช้า: {e}")

        # ---------------------------------------------------------
        # STEP 3: Smart Wait
        # ---------------------------------------------------------
        print("⏳ รอเนื้อหางาน...")
        if not smart_wait_for_jobs(page):
            print("❌ หาไม่เจอ — บันทึก screenshot ไว้ debug")
            page.screenshot(path="cloud_failed.png")
            browser.close()
            conn.close()
            return

        save_cookies(context)

        # ---------------------------------------------------------
        # STEP 4: ดึงข้อมูลทีละหน้า → upsert เข้า DB
        # ---------------------------------------------------------
        for current_page in range(1, max_pages + 1):
            target_url = f"{search_url}?page={current_page}"
            print(f"\n📄 หน้าที่ {current_page}/{max_pages}")

            try:
                page.goto(target_url, timeout=60000)
                human_like_mouse(page)
                human_like_scroll(page)

                if not smart_wait_for_jobs(page, max_retries=15):
                    print(f"⚠️ หน้า {current_page} ไม่เจอ job listing → ข้ามไป")
                    continue

                job_cards, method = find_job_cards(page)
                print(f"✅ เจอ {len(job_cards)} งาน ({method})")

                if len(job_cards) == 0:
                    print("⚠️ ไม่เจองาน → จบ")
                    break

                # Loop เก็บ + upsert ทีละ card
                skipped = 0
                for i, card in enumerate(job_cards):
                    try:
                        job_data = extract_job_data(card)

                        # Dedup Layer 1: Link
                        if job_data['Link'] in existing_links:
                            skipped += 1
                            continue

                        # Dedup Layer 2: Fingerprint
                        fp = make_fingerprint(
                            job_data.get('Title'), job_data.get('Company'),
                            job_data.get('Location'), job_data.get('Salary')
                        )
                        if fp in existing_fingerprints:
                            skipped += 1
                            continue

                        # Upsert เข้า DB ทันที
                        job_id = upsert_job(conn, job_data)
                        if job_id:
                            new_count += 1
                            print(f"   ✅ [{new_count}] {job_data['Title'][:50]} (id={job_id})")

                        existing_links.add(job_data['Link'])
                        existing_fingerprints.add(fp)

                    except Exception as e:
                        print(f"   ⚠️ ข้ามงานที่ {i+1}: {e}")
                        continue

                skipped_total += skipped
                if skipped > 0:
                    print(f"   ⏭️ ข้ามงานซ้ำ {skipped} งาน")

                # พักก่อนไปหน้าถัดไป
                sleep_time = random.uniform(5, 10)
                print(f"💤 พัก {sleep_time:.1f}s...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"❌ Error หน้า {current_page}: {e}")
                continue

        # บันทึก cookies สุดท้าย
        save_cookies(context)
        browser.close()

    conn.close()

    # ---------------------------------------------------------
    # สรุปผล
    # ---------------------------------------------------------
    print(f"\n{'='*50}")
    print(f"🎉 Phase 1 เสร็จสิ้น!")
    print(f"   🆕 งานใหม่ที่ upsert: {new_count}")
    print(f"   ⏭️ ข้ามงานซ้ำ: {skipped_total}")
    print(f"   📊 งานรวมใน DB: {len(existing_links)}")
    print(f"{'='*50}")


if __name__ == '__main__':
    run()
