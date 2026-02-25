"""
Scraper DB Helper — Shared utilities for cloud scraping pipeline
รวม Database connection, Anti-Detection helpers, และ User-Agent Pool
"""
import psycopg2
import os
import time
import random
import json
from dotenv import load_dotenv

# โหลด .env จาก root ของโปรเจกต์
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

DATABASE_URL = os.getenv('DATABASE_URL', '')

# ============================================================
# Browser Config — headless toggle สำหรับ CI/Local
# ============================================================
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

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


# ============================================================
# Database Helpers
# ============================================================
def get_connection():
    """Connect to Supabase PostgreSQL via DATABASE_URL"""
    if not DATABASE_URL:
        raise ValueError("❌ DATABASE_URL not set in .env")
    return psycopg2.connect(DATABASE_URL)


def get_existing_links(conn) -> set:
    """ดึง link ทั้งหมดที่มีอยู่ใน jobs table (สำหรับ dedup)"""
    cur = conn.cursor()
    cur.execute("SELECT link FROM jobs WHERE link IS NOT NULL")
    links = set(row[0] for row in cur.fetchall())
    cur.close()
    return links


def upsert_job(conn, job_data: dict) -> int | None:
    """
    Insert job เข้า jobs table (ON CONFLICT DO NOTHING)
    ใส่แค่ข้อมูลเบื้องต้น: Title, Company, Location, Salary, Link
    Returns: job id ถ้า insert สำเร็จ, None ถ้ามีอยู่แล้ว
    """
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (title, company, location, salary, link)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (link) DO NOTHING
        RETURNING id
    """, (
        job_data.get('Title', ''),
        job_data.get('Company', ''),
        job_data.get('Location', ''),
        job_data.get('Salary', ''),
        job_data.get('Link', ''),
    ))
    result = cur.fetchone()
    conn.commit()
    cur.close()
    return result[0] if result else None


def update_description(conn, link: str, jd_text: str):
    """Update description ของ job ที่มี link ตรงกัน"""
    cur = conn.cursor()
    cur.execute("""
        UPDATE jobs SET description = %s, updated_at = NOW()
        WHERE link = %s
    """, (jd_text, link))
    conn.commit()
    cur.close()


def get_pending_jobs(conn) -> list[tuple]:
    """
    ดึงรายการ jobs ที่ยังไม่มี JD (description IS NULL หรือเป็น Error)
    Returns: list ของ (id, link, title)
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT id, link, title FROM jobs
        WHERE description IS NULL 
           OR description IN ('', 'Error')
        ORDER BY id
    """)
    results = cur.fetchall()
    cur.close()
    return results


# ============================================================
# Browser Config Helper
# ============================================================
def get_browser_config() -> dict:
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
# Cookie Helpers (สำหรับ Cloud — อ่านจาก env var)
# ============================================================
COOKIES_FILE = "jobsdb_cookies.json"


def load_cookies(context) -> bool:
    """
    โหลด cookies — ลำดับการค้นหา:
    1. env var JOBSDB_COOKIES (JSON string) — สำหรับ GitHub Actions
    2. ไฟล์ jobsdb_cookies.json — สำหรับ local
    """
    # 1. จาก env var (GitHub Actions Secret)
    cookies_env = os.getenv("JOBSDB_COOKIES", "")
    if cookies_env:
        try:
            cookies = json.loads(cookies_env)
            context.add_cookies(cookies)
            print(f"🍪 โหลด cookies จาก env var ({len(cookies)} cookies)")
            return True
        except json.JSONDecodeError:
            print("⚠️ JOBSDB_COOKIES env var ไม่ใช่ JSON ที่ถูกต้อง")

    # 2. จากไฟล์ local
    cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), COOKIES_FILE)
    if os.path.exists(cookies_path):
        with open(cookies_path, 'r') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print(f"🍪 โหลด cookies จากไฟล์ ({len(cookies)} cookies)")
        return True

    print("🍪 ไม่มี cookies — จะเริ่มต้นใหม่")
    return False


def save_cookies(context):
    """บันทึก cookies ลงไฟล์ (สำหรับ local dev)"""
    cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), COOKIES_FILE)
    cookies = context.cookies()
    with open(cookies_path, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"🍪 บันทึก cookies แล้ว ({len(cookies)} cookies)")


# ============================================================
# Cloudflare Turnstile Solver
# ============================================================
def solve_cloudflare_turnstile(page, max_attempts: int = 3):
    """
    ตรวจจับและพยายามคลิกผ่าน Cloudflare Turnstile ("ยืนยันว่าคุณเป็นมนุษย์")
    เรียกหลัง page.goto() ทุกครั้ง เพื่อป้องกันไม่ให้ script ไปหา selector ขณะติด Cloudflare
    """
    for attempt in range(1, max_attempts + 1):
        try:
            # เช็คว่ามี Turnstile iframe ไหม (รอ 5 วินาที)
            iframe_el = page.wait_for_selector(
                "iframe[src*='challenges.cloudflare.com']", timeout=5000
            )
            if not iframe_el:
                print("   ✅ ไม่ติด Cloudflare")
                return True

            print(f"   🛡️ เจอ Cloudflare Turnstile! (attempt {attempt}/{max_attempts})")

            # ขยับเมาส์ไปหา iframe แบบมนุษย์
            box = iframe_el.bounding_box()
            if box:
                # เลื่อนเมาส์ไปที่กล่อง checkbox อย่างช้าๆ
                target_x = box['x'] + 35  # checkbox อยู่ทางซ้ายของ iframe
                target_y = box['y'] + box['height'] / 2
                page.mouse.move(target_x, target_y, steps=random.randint(15, 30))
                time.sleep(random.uniform(0.5, 1.5))

            # เข้าไปใน iframe เพื่อคลิก checkbox
            frame = iframe_el.content_frame()
            if frame:
                # ลองหา checkbox ด้วยหลาย selector
                for selector in [
                    "input[type='checkbox']",
                    ".ctp-checkbox-label",
                    "#challenge-stage",
                    "label",
                ]:
                    el = frame.locator(selector)
                    if el.count() > 0:
                        el.first.click(force=True)
                        print(f"   🖱️ คลิก checkbox แล้ว ({selector})")
                        break

            # รอให้ Cloudflare ตรวจสอบเสร็จ
            time.sleep(random.uniform(5, 8))

            # เช็คว่าผ่านแล้วหรือยัง (ถ้า iframe หายไป = ผ่าน)
            remaining = page.locator("iframe[src*='challenges.cloudflare.com']").count()
            if remaining == 0:
                print("   ✅ ผ่าน Cloudflare แล้ว!")
                # รอให้หน้าเว็บจริงโหลด
                time.sleep(random.uniform(2, 4))
                return True
            else:
                print(f"   ⏳ ยังไม่ผ่าน... (attempt {attempt})")

        except Exception:
            # ไม่เจอ iframe ใน 5 วินาที = หน้าเว็บปกติ ไม่ติด Cloudflare
            print("   ✅ ไม่ติด Cloudflare")
            return True

    print("   ❌ ไม่สามารถผ่าน Cloudflare ได้")
    page.screenshot(path="cloudflare_blocked.png")
    return False


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


def smart_delay(index: int, total: int, long_break_every: int = 25):
    """หน่วงเวลาอัจฉริยะ — พักยาวเป็นระยะ"""
    if (index + 1) % long_break_every == 0 and index < total - 1:
        sleep_time = random.uniform(30, 60)
        print(f"   ☕ พักยาว {sleep_time:.0f}s ({index+1}/{total} เสร็จแล้ว)...")
        time.sleep(sleep_time)
    else:
        time.sleep(random.uniform(5, 15))


def normalize_link(url: str) -> str:
    """ลบ tracking params ออกจาก JobsDB URL"""
    if not url or url == "N/A":
        return url
    return url.split('?')[0].split('#')[0]


def make_fingerprint(title, company, location=None, salary=None) -> tuple:
    """สร้าง fingerprint จาก Title+Company+Location+Salary เพื่อจับ duplicate"""
    def _clean(val):
        if val is None or (isinstance(val, float) and str(val) == 'nan'):
            return ''
        return str(val).strip().lower()
    return (_clean(title), _clean(company), _clean(location), _clean(salary))
