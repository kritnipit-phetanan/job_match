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
OUTPUT_FILE = "jobsdb_result_all.csv"

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

# ============================================================
# ไฟล์ที่เก็บ Cookies (จะถูกสร้าง/อ่านอัตโนมัติ)
# ============================================================
COOKIES_FILE = "jobsdb_cookies.json"


def save_cookies(context, filepath=COOKIES_FILE):
    """บันทึก cookies ลงไฟล์ JSON"""
    cookies = context.cookies()
    with open(filepath, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"🍪 บันทึก cookies แล้ว ({len(cookies)} cookies) -> {filepath}")


def load_cookies(context, filepath=COOKIES_FILE):
    """โหลด cookies จากไฟล์ JSON (ถ้ามี)"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print(f"🍪 โหลด cookies จากไฟล์แล้ว ({len(cookies)} cookies)")
        return True
    else:
        print("🍪 ไม่มีไฟล์ cookies เก่า จะเริ่มต้นใหม่")
        return False


def login_and_save_cookies():
    """
    เปิด Chrome จริง (ไม่ใช่ Chromium ของ Playwright) เพื่อให้ Login Google ได้
    ใช้ persistent context เพื่อเก็บ browser profile ไว้ในโฟลเดอร์ chrome_profile/
    รันครั้งเดียว แล้วใช้ cookies ต่อได้เรื่อยๆ จนกว่า session จะหมดอายุ
    """
    # สร้างโฟลเดอร์เก็บ profile ถ้ายังไม่มี
    profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")
    os.makedirs(profile_dir, exist_ok=True)

    with sync_playwright() as p:
        print("🔑 เปิด Chrome จริง (ไม่ใช่ Chromium) เพื่อ Login...")
        print("   👉 ใช้ Chrome จริงในเครื่อง → Google จะอนุญาตให้ Login ผ่าน")
        print("   👉 กรุณา Login ที่หน้าเว็บ JobsDB ให้เสร็จ")
        print("   👉 เมื่อ Login สำเร็จแล้ว ให้กลับมาพิมพ์ Enter ที่ Terminal นี้\n")

        # launch_persistent_context ใช้ Chrome จริง + เก็บ profile
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            channel="chrome",          # <<<< ใช้ Chrome จริงที่ติดตั้งในเครื่อง
            headless=False,
            viewport={'width': 1280, 'height': 800},
            locale='th-TH',
            args=[
                '--disable-blink-features=AutomationControlled',  # ซ่อน automation flag
            ],
        )
        page = context.new_page()

        # ไปหน้า login
        page.goto("https://th.jobsdb.com/", timeout=60000)

        # รอให้ user login เอง
        input("✅ Login เสร็จแล้ว? กด Enter เพื่อบันทึก cookies...")

        # บันทึก cookies
        save_cookies(context)

        context.close()
        print("🎉 บันทึก cookies เรียบร้อย! สามารถรัน scrape ได้เลย")
        print(f"📁 Profile ถูกเก็บไว้ที่: {profile_dir}")


def find_job_cards(page):
    """
    ลองหา job cards ด้วยหลาย selectors (เผื่อ JobsDB เปลี่ยน)
    คืนค่า (list_of_cards, method_name)
    """
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


def normalize_link(url: str) -> str:
    """
    ลบ tracking params ออกจาก JobsDB URL เพื่อให้ dedup ได้ถูกต้อง
    เช่น https://th.jobsdb.com/job/89785363?type=standard&ref=search-standalone#sol=b4696
      → https://th.jobsdb.com/job/89785363
    """
    if not url or url == "N/A":
        return url
    # ตัด query string และ fragment ออก
    url = url.split('?')[0].split('#')[0]
    return url


def _make_fingerprint(title, company, location=None, salary=None) -> tuple:
    """
    สร้าง fingerprint จาก Title+Company+Location+Salary เพื่อจับ duplicate ข้าม URL
    Normalize: lowercase, strip whitespace, แปลง NaN เป็น empty string
    """
    def _clean(val):
        if val is None or (isinstance(val, float) and str(val) == 'nan'):
            return ''
        return str(val).strip().lower()
    
    return (_clean(title), _clean(company), _clean(location), _clean(salary))


def extract_job_data(card):
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


def smart_wait_for_jobs(page, max_retries=30):
    """
    วนลูปรอจนกว่าจะเจอ job cards (ลองหลาย selector)
    คืน True ถ้าเจอ, False ถ้าหมดเวลา
    """
    for i in range(max_retries):
        cards, method = find_job_cards(page)
        if len(cards) > 0:
            print(f"✅ เจอ Job Listing แล้ว! ({method}, {len(cards)} cards)")
            return True

        # Scroll เพื่อกระตุ้น lazy load
        page.mouse.wheel(0, 300)
        print(f"   ...รอ ({i+1}/{max_retries}) - ยังไม่เจอ selector")
        time.sleep(2)

    return False


def run():
    # ============================================================
    # ตั้งค่า
    # ============================================================
    keyword = "data engineer"
    max_pages = 5
    formatted_keyword = keyword.replace(" ", "-").lower()

    home_url = "https://th.jobsdb.com/"
    search_url = f'https://th.jobsdb.com/{formatted_keyword}-jobs'

    all_jobs = []

    # ---------------------------------------------------------
    # โหลดข้อมูลเก่า → เพื่อข้ามงานซ้ำ (Multi-layer dedup)
    # ---------------------------------------------------------
    existing_links = set()
    existing_fingerprints = set()  # (Title, Company, Location, Salary)
    df_existing = None
    if os.path.exists(OUTPUT_FILE):
        df_existing = pd.read_csv(OUTPUT_FILE)
        # Normalize links ที่มีอยู่แล้ว
        df_existing['Link'] = df_existing['Link'].apply(normalize_link)
        existing_links = set(df_existing['Link'].dropna())
        # สร้าง fingerprint จาก Title+Company+Location+Salary
        for _, r in df_existing.iterrows():
            fp = _make_fingerprint(r.get('Title'), r.get('Company'), r.get('Location'), r.get('Salary'))
            existing_fingerprints.add(fp)
        print(f"📋 พบข้อมูลเก่าใน {OUTPUT_FILE}: {len(df_existing)} งาน (จะข้ามงานซ้ำ)")
    else:
        print(f"📋 ยังไม่มีไฟล์ {OUTPUT_FILE} → จะสร้างใหม่")

    with sync_playwright() as p:
        print("🚀 เริ่มต้นระบบ...")
        browser_config = get_browser_config()
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=browser_config["user_agent"],
            extra_http_headers=browser_config["extra_http_headers"],
            viewport={'width': 1280, 'height': 800},
            locale='th-TH'
        )

        # ---------------------------------------------------------
        # โหลด Login Session Cookies (ถ้ามี)
        # ---------------------------------------------------------
        has_cookies = load_cookies(context)

        page = context.new_page()

        # Apply Stealth
        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        # ---------------------------------------------------------
        # STEP 1: เข้าหน้าแรก (Warm-up) เพื่อรับ/ยืนยัน Cookies
        # ---------------------------------------------------------
        print(f"1️⃣ กำลังเข้าหน้าแรก: {home_url}")
        try:
            page.goto(home_url, timeout=60000)
            # รอนานขึ้นหน่อย ให้ cookies ทำงานเต็มที่
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            print(f"⚠️ เข้าหน้าแรกช้า: {e} แต่จะพยายามไปต่อ...")

        # ขยับเมาส์หลอกๆ (Random Mouse Movement)
        print("🖱️ กำลังขยับเมาส์เลียนแบบมนุษย์...")
        for _ in range(random.randint(3, 7)):
            x = random.randint(100, 1000)
            y = random.randint(100, 700)
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.2, 0.8))

        # บันทึก cookies ใหม่ (เผื่อเว็บ set cookies เพิ่มจากหน้าแรก)
        save_cookies(context)

        # ---------------------------------------------------------
        # STEP 2: ไปหน้าค้นหา
        # ---------------------------------------------------------
        print(f"2️⃣ กำลังไปหน้าค้นหา: {search_url}")
        try:
            page.goto(search_url, timeout=60000)
        except Exception as e:
            print(f"⚠️ เข้าหน้าค้นหาช้า: {e}")

        # ---------------------------------------------------------
        # STEP 3: ระบบรออัจฉริยะ (Smart Wait)
        # ---------------------------------------------------------
        print("⏳ กำลังรอเนื้อหางาน...")
        print("   (ถ้าเห็นหน้าเว็บแล้ว แต่ Script ยังนิ่ง ให้ลอง Scroll เมาส์ช่วย)")

        if not smart_wait_for_jobs(page):
            print("❌ หาไม่เจอจริงๆ ขอ Snapshot หน้าจอ + HTML ไว้ debug")
            page.screenshot(path="failed_final.png")
            # บันทึก HTML ด้วย เพื่อดู structure จริง
            with open("failed_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("   📸 ดู failed_final.png และ failed_page.html เพื่อ debug")
            browser.close()
            return

        # อัพเดท cookies อีกรอบหลังผ่าน challenge
        save_cookies(context)

        # ---------------------------------------------------------
        # STEP 4: ดึงข้อมูลทีละหน้า
        # ---------------------------------------------------------
        for current_page in range(1, max_pages + 1):
            target_url = f"{search_url}?page={current_page}"
            print(f"\n📄 กำลังดึงข้อมูล หน้าที่ {current_page}/{max_pages}")
            print(f"🔗 URL: {target_url}")

            try:
                page.goto(target_url, timeout=60000)

                # Anti-detection: ขยับเมาส์ + เลื่อนหน้าจอแบบมนุษย์
                print("⏳ รอเนื้อหาโหลด...")
                human_like_mouse(page)
                human_like_scroll(page)

                # ใช้ smart wait แทน wait_for_selector ตัวเดียว
                if not smart_wait_for_jobs(page, max_retries=15):
                    print(f"⚠️ หน้า {current_page} ไม่เจอ job listing -> ข้ามไป")
                    continue

                # ดึง Card ทั้งหมดในหน้า
                job_cards, method = find_job_cards(page)
                print(f"✅ หน้า {current_page} เจอ {len(job_cards)} งาน ({method})")

                if len(job_cards) == 0:
                    print("⚠️ ไม่เจองานในหน้านี้ -> จบการทำงาน")
                    break

                # Loop เก็บข้อมูลในหน้า
                skipped = 0
                for i, card in enumerate(job_cards):
                    try:
                        job_data = extract_job_data(card)
                        
                        # ===== Multi-layer dedup =====
                        # ชั้น 1: Normalized Link ซ้ำ
                        if job_data['Link'] in existing_links:
                            skipped += 1
                            continue
                        # ชั้น 2: Title+Company+Location+Salary ซ้ำ
                        fp = _make_fingerprint(
                            job_data.get('Title'), job_data.get('Company'),
                            job_data.get('Location'), job_data.get('Salary')
                        )
                        if fp in existing_fingerprints:
                            skipped += 1
                            continue
                        
                        # ไม่ซ้ำ → เก็บ + เพิ่มเข้า set ป้องกันซ้ำในรอบเดียวกัน
                        all_jobs.append(job_data)
                        existing_links.add(job_data['Link'])
                        existing_fingerprints.add(fp)
                    except Exception as e:
                        print(f"   ⚠️ ข้ามงานที่ {i+1}: {e}")
                        continue

                if skipped > 0:
                    print(f"   ⏭️ ข้ามงานซ้ำ {skipped} งาน")
                print(f"📊 งานใหม่สะสม: {len(all_jobs)} งาน")

                # พักก่อนไปหน้าถัดไป
                sleep_time = random.uniform(5, 10)
                print(f"💤 พัก {sleep_time:.1f} วินาที ก่อนไปหน้าต่อไป...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"❌ Error หน้า {current_page}: {e}")
                continue

        # ---------------------------------------------------------
        # STEP 5: บันทึกผลลัพธ์ (append เข้าข้อมูลเก่า)
        # ---------------------------------------------------------
        if all_jobs:
            df_new = pd.DataFrame(all_jobs)
            # Dedup ภายใน batch ใหม่
            df_new.drop_duplicates(subset=['Link'], inplace=True)
            df_new.drop_duplicates(subset=['Title', 'Company', 'Location', 'Salary'], inplace=True)

            # Append เข้ากับข้อมูลเก่า (ถ้ามี)
            if df_existing is not None and len(df_existing) > 0:
                df_final = pd.concat([df_existing, df_new], ignore_index=True)
                df_final.drop_duplicates(subset=['Link'], keep='last', inplace=True)
                df_final.drop_duplicates(subset=['Title', 'Company', 'Location', 'Salary'], keep='last', inplace=True)
            else:
                df_final = df_new

            df_final.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
            print(f"\n🎉🎉 เสร็จสิ้น!")
            print(f"   🆕 งานใหม่รอบนี้: {len(df_new)} งาน")
            print(f"   📊 งานรวมทั้งหมดใน {OUTPUT_FILE}: {len(df_final)} งาน")
        else:
            print("\n✅ ไม่มีงานใหม่ ทุกงานมีอยู่ใน CSV แล้ว!")

        # บันทึก cookies สุดท้าย
        save_cookies(context)

        time.sleep(3)
        browser.close()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--login':
        login_and_save_cookies()
    else:
        run()