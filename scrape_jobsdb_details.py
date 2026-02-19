from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import pandas as pd
import time
import random
import json
import os

# ============================================================
# ตั้งค่า
# ============================================================
COOKIES_FILE = "jobsdb_cookies.json"
INPUT_FILE = "jobsdb_result_all.csv"       # ผลจาก scrape_jobsdb.py
OUTPUT_FILE = "jobsdb_full_data.csv"       # ผลลัพธ์รวม JD
BROKEN_LINK_FLAG = "Not Found"              # Flag สำหรับลิงก์เสีย → ข้ามเมื่อรันใหม่

# User-Agent Pool (สลับ Chrome 143/144/145 พร้อม Build จริง)
UA_POOL = [
    {
        "version": "143",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7449.68 Safari/537.36",
        "sec_ch_ua": '"Google Chrome";v="143", "Chromium";v="143", "Not?A_Brand";v="99"',
    },
    {
        "version": "144",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7540.95 Safari/537.36",
        "sec_ch_ua": '"Google Chrome";v="144", "Chromium";v="144", "Not?A_Brand";v="99"',
    },
    {
        "version": "145",
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.76 Safari/537.36",
        "sec_ch_ua": '"Google Chrome";v="145", "Chromium";v="145", "Not?A_Brand";v="99"',
    },
]


def get_browser_config():
    """สุ่ม User-Agent + Client Hints headers ที่สอดคล้องกัน"""
    profile = random.choice(UA_POOL)
    print(f"🌐 ใช้ Chrome/{profile['version']} สำหรับรอบนี้")
    return {
        "user_agent": profile["ua"],
        "extra_http_headers": {
            "sec-ch-ua": profile["sec_ch_ua"],
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
        },
    }

# Anti-detection settings
DELAY_MIN = 5           # วินาทีขั้นต่ำระหว่างงาน
DELAY_MAX = 15          # วินาทีสูงสุดระหว่างงาน
LONG_BREAK_EVERY = 25   # พักยาวทุกๆ N งาน
LONG_BREAK_MIN = 30     # วินาทีขั้นต่ำพักยาว
LONG_BREAK_MAX = 60     # วินาทีสูงสุดพักยาว


# ============================================================
# Cookie Helpers
# ============================================================
def load_cookies(context, filepath=COOKIES_FILE):
    """โหลด cookies จากไฟล์ JSON"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print(f"🍪 โหลด cookies แล้ว ({len(cookies)} cookies)")
        return True
    else:
        print("⚠️ ไม่มี jobsdb_cookies.json → รัน 'python scrape_jobsdb.py --login' ก่อน!")
        return False


def save_cookies(context, filepath=COOKIES_FILE):
    """บันทึก cookies ลงไฟล์"""
    cookies = context.cookies()
    with open(filepath, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"🍪 บันทึก cookies แล้ว ({len(cookies)} cookies)")


# ============================================================
# Anti-Detection Helpers
# ============================================================
def human_like_scroll(page):
    """เลื่อนหน้าจอแบบมนุษย์"""
    scroll_times = random.randint(2, 5)
    for _ in range(scroll_times):
        page.mouse.wheel(0, random.randint(200, 600))
        time.sleep(random.uniform(0.3, 1.0))
    # เลื่อนกลับขึ้นบ้าง (มนุษย์จริงทำแบบนี้)
    if random.random() > 0.5:
        page.mouse.wheel(0, -random.randint(100, 300))
        time.sleep(random.uniform(0.2, 0.5))


def human_like_mouse(page):
    """ขยับเมาส์แบบมนุษย์"""
    for _ in range(random.randint(2, 4)):
        x = random.randint(100, 1000)
        y = random.randint(100, 600)
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.1, 0.4))


def smart_delay(index, total):
    """หน่วงเวลาอัจฉริยะ - พักยาวเป็นระยะ"""
    # พักยาวทุกๆ LONG_BREAK_EVERY งาน
    if (index + 1) % LONG_BREAK_EVERY == 0 and index < total - 1:
        sleep_time = random.uniform(LONG_BREAK_MIN, LONG_BREAK_MAX)
        print(f"   ☕ พักยาว {sleep_time:.0f} วินาที ({index+1}/{total} งานเสร็จแล้ว)...")
        time.sleep(sleep_time)
    else:
        # พักปกติ (แต่สุ่มให้หลากหลาย)
        sleep_time = random.uniform(DELAY_MIN, DELAY_MAX)
        time.sleep(sleep_time)


# ============================================================
# Main
# ============================================================
def run():
    # ---------------------------------------------------------
    # 1. อ่านไฟล์ input (งานทั้งหมดจาก scraper)
    # ---------------------------------------------------------
    try:
        df_input = pd.read_csv(INPUT_FILE)
        print(f"📂 โหลดข้อมูลจาก {INPUT_FILE}: {len(df_input)} งาน")
    except FileNotFoundError:
        print(f"❌ หาไฟล์ {INPUT_FILE} ไม่เจอ! (ต้องรัน scrape_jobsdb.py ก่อน)")
        return

    # กรองเฉพาะแถวที่มี Link จริง
    df_input = df_input[df_input['Link'].notna() & (df_input['Link'] != 'N/A')].reset_index(drop=True)

    # ---------------------------------------------------------
    # 2. ตรวจสอบข้อมูลเก่า → ข้ามงานที่เคย scrape แล้ว
    # ---------------------------------------------------------
    df_existing = None
    already_scraped_links = set()
    broken_links = set()

    if os.path.exists(OUTPUT_FILE):
        df_existing = pd.read_csv(OUTPUT_FILE)
        # นับเฉพาะงานที่มี JD จริงๆ (ไม่ใช่ Not Found / Error)
        scraped_mask = (
            df_existing['JobDescription'].notna() &
            ~df_existing['JobDescription'].isin([BROKEN_LINK_FLAG, "Error", "No Link", ""])
        )
        already_scraped_links = set(df_existing.loc[scraped_mask, 'Link'].dropna())

        # ลิงก์เสีย (flag = "Not Found") → ข้ามเมื่อรันใหม่
        broken_mask = df_existing['JobDescription'] == BROKEN_LINK_FLAG
        broken_links = set(df_existing.loc[broken_mask, 'Link'].dropna())

        print(f"📋 พบข้อมูลเก่าใน {OUTPUT_FILE}: {len(df_existing)} งาน (มี JD แล้ว {len(already_scraped_links)} งาน)")
        if broken_links:
            print(f"🚩 ลิงก์เสีย (flagged): {len(broken_links)} งาน → ข้าม")

    # หางานใหม่ที่ยังไม่เคย scrape (ข้ามทั้งงานที่มี JD แล้วและลิงก์เสีย)
    skip_links = already_scraped_links | broken_links
    df_new = df_input[~df_input['Link'].isin(skip_links)].reset_index(drop=True)

    print(f"\n📊 สรุป:")
    print(f"   งานทั้งหมดใน {INPUT_FILE}: {len(df_input)} งาน")
    print(f"   เคย scrape JD แล้ว:        {len(already_scraped_links)} งาน")
    print(f"   🚩 ลิงก์เสีย (ข้าม):        {len(broken_links)} งาน")
    print(f"   🆕 งานใหม่ที่ต้อง scrape:   {len(df_new)} งาน\n")

    if len(df_new) == 0:
        print("✅ ไม่มีงานใหม่ ทุกงานถูก scrape หมดแล้ว!")
        return

    # ---------------------------------------------------------
    # 3. เริ่ม Scrape งานใหม่
    # ---------------------------------------------------------
    new_results = []

    with sync_playwright() as p:
        browser_config = get_browser_config()
        browser = p.chromium.launch(headless=False)
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
        except Exception as e:
            print(f"⚠️ Warm-up ช้า: {e}")

        print(f"🚀 เริ่มเจาะข้อมูล {len(df_new)} งานใหม่...\n")

        for index, row in df_new.iterrows():
            url = row['Link']
            title = row['Title']

            print(f"[{index+1}/{len(df_new)}] กำลังเข้า: {title[:50]}...")

            try:
                page.goto(url, timeout=30000)

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
                    row_data = row.to_dict()
                    row_data['JobDescription'] = jd_text
                    new_results.append(row_data)
                    print(f"   ✅ ดึง JD สำเร็จ! ({len(jd_text)} ตัวอักษร)")
                else:
                    row_data = row.to_dict()
                    row_data['JobDescription'] = BROKEN_LINK_FLAG
                    new_results.append(row_data)
                    print(f"   ⚠️ หา JD ไม่เจอ → flagged เป็น '{BROKEN_LINK_FLAG}' (จะข้ามในรอบถัดไป)")

            except Exception as e:
                row_data = row.to_dict()
                row_data['JobDescription'] = "Error"
                new_results.append(row_data)
                print(f"   ❌ Error: {e}")

            # หน่วงเวลาอัจฉริยะ
            smart_delay(index, len(df_new))

        # บันทึก cookies
        save_cookies(context)
        browser.close()

    # ---------------------------------------------------------
    # 4. รวมข้อมูลเก่า + ข้อมูลใหม่ แล้วบันทึก
    # ---------------------------------------------------------
    df_new_results = pd.DataFrame(new_results)

    if df_existing is not None and len(df_existing) > 0:
        # รวมข้อมูลเก่า + ใหม่
        df_final = pd.concat([df_existing, df_new_results], ignore_index=True)
        # ลบซ้ำ (เก็บตัวหลังสุด = ข้อมูลใหม่กว่า)
        df_final.drop_duplicates(subset=['Link'], keep='last', inplace=True)
    else:
        df_final = df_new_results

    df_final.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    # สรุปผล
    success_count = sum(1 for r in new_results if r['JobDescription'] not in [BROKEN_LINK_FLAG, "Error"])
    flagged_count = sum(1 for r in new_results if r['JobDescription'] == BROKEN_LINK_FLAG)
    error_count = sum(1 for r in new_results if r['JobDescription'] == "Error")
    print(f"\n{'='*50}")
    print(f"🎉🎉 เสร็จสมบูรณ์!")
    print(f"   🆕 งานใหม่ที่ scrape รอบนี้: {len(new_results)} งาน")
    print(f"   ✅ ดึง JD ได้: {success_count}/{len(new_results)} งาน")
    if flagged_count:
        print(f"   🚩 ลิงก์เสีย (flagged):     {flagged_count} งาน (จะข้ามในรอบถัดไป)")
    if error_count:
        print(f"   ❌ Error (จะ retry รอบถัดไป): {error_count} งาน")
    print(f"   📊 ข้อมูลรวมทั้งหมดใน {OUTPUT_FILE}: {len(df_final)} งาน")
    print(f"{'='*50}")


if __name__ == '__main__':
    run()