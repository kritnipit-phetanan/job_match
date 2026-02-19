"""
Scraping Health Check — ตรวจสอบว่า HTML selectors ของ JobsDB ยังใช้งานได้
ใช้: python -m test.health_check
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import random
import sys

# ============================================================
# Selectors ที่ใช้ใน scraper (ต้อง sync กับ scrape_jobsdb.py / scrape_jobsdb_details.py)
# ============================================================

# Job listing selectors (จาก scrape_jobsdb.py → find_job_cards)
LISTING_SELECTORS = [
    ('[data-automation="jobListing"]',       "data-automation=jobListing"),
    ('div[data-search-sol-meta]',            "data-search-sol-meta"),
    ('article[data-card-type="JobCard"]',    "article JobCard"),
    ('article[data-job-id]',                 "article data-job-id"),
    ('div[data-job-id]',                     "div data-job-id"),
    ('article',                              "article (generic)"),
]

# Job detail selectors (จาก scrape_jobsdb_details.py)
DETAIL_SELECTORS = [
    ('[data-automation="jobDescription"]',   "data-automation=jobDescription"),
    ('div[data-automation="job-details"]',   "data-automation=job-details"),
    ('[data-automation="jobAdDetails"]',     "data-automation=jobAdDetails"),
    ('div[class*="jobDescription"]',         "class*=jobDescription"),
    ('div[class*="job-description"]',        "class*=job-description"),
]

# UA (ใช้ตัวเดียวก็พอสำหรับ health check)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.76 Safari/537.36"

# URLs
LISTING_URL = "https://th.jobsdb.com/data-engineer-jobs"
SAMPLE_JOB_URL = None  # จะดึงจากหน้า listing


def check_listing_page(page) -> dict:
    """ตรวจสอบ selectors ของหน้า listing"""
    print(f"\n{'='*60}")
    print(f"🔍 ตรวจหน้า Job Listing: {LISTING_URL}")
    print(f"{'='*60}")

    page.goto(LISTING_URL, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(5000)

    results = {"url": LISTING_URL, "selectors": {}, "working": False, "first_job_link": None}

    for selector, name in LISTING_SELECTORS:
        count = page.locator(selector).count()
        status = "✅" if count > 0 else "❌"
        results["selectors"][name] = {"count": count, "working": count > 0}
        print(f"   {status} {name}: {count} elements")

        if count > 0 and not results["working"]:
            results["working"] = True
            # ดึง link ตัวแรกเพื่อใช้ test detail page
            try:
                first_card = page.locator(selector).first
                link_el = first_card.locator('a[href*="/job/"]').first
                if link_el.count() > 0:
                    href = link_el.get_attribute('href')
                    if href:
                        results["first_job_link"] = href if href.startswith('http') else f"https://th.jobsdb.com{href}"
            except Exception:
                pass

    if results["working"]:
        print(f"\n   ✅ หน้า Listing ทำงานได้!")
    else:
        print(f"\n   ❌ ไม่มี selector ตัวไหนใช้ได้! JobsDB อาจเปลี่ยน HTML structure")

    return results


def check_detail_page(page, job_url: str) -> dict:
    """ตรวจสอบ selectors ของหน้า job detail"""
    print(f"\n{'='*60}")
    print(f"🔍 ตรวจหน้า Job Detail: {job_url[:80]}...")
    print(f"{'='*60}")

    page.goto(job_url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(5000)

    results = {"url": job_url, "selectors": {}, "working": False, "jd_preview": None}

    for selector, name in DETAIL_SELECTORS:
        count = page.locator(selector).count()
        status = "✅" if count > 0 else "❌"
        results["selectors"][name] = {"count": count, "working": count > 0}
        print(f"   {status} {name}: {count} elements")

        if count > 0 and not results["working"]:
            results["working"] = True
            try:
                text = page.locator(selector).first.inner_text().strip()
                results["jd_preview"] = text[:200]
            except Exception:
                pass

    if results["working"]:
        print(f"\n   ✅ หน้า Detail ทำงานได้!")
        if results["jd_preview"]:
            print(f"   📄 Preview: {results['jd_preview'][:100]}...")
    else:
        print(f"\n   ❌ ไม่มี selector ตัวไหนใช้ได้! JobsDB อาจเปลี่ยน HTML structure")

    return results


def run_health_check():
    """รัน health check ทั้งหมด"""
    print("🏥 JobsDB Scraping Health Check")
    print(f"   เวลา: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={'width': 1280, 'height': 800},
            locale='th-TH',
        )

        page = context.new_page()

        # Apply stealth
        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        # 1. ตรวจหน้า listing
        listing_result = check_listing_page(page)

        # 2. ตรวจหน้า detail (ใช้ link จาก listing หรือ arg)
        job_url = SAMPLE_JOB_URL or listing_result.get("first_job_link")
        detail_result = None

        if job_url:
            page.wait_for_timeout(random.randint(2000, 4000))
            detail_result = check_detail_page(page, job_url)
        else:
            print("\n⚠️ ไม่มี job link สำหรับทดสอบหน้า detail")

        browser.close()

    # สรุป
    print(f"\n{'='*60}")
    print("📊 สรุป Health Check")
    print(f"{'='*60}")

    all_ok = True

    listing_ok = listing_result["working"]
    print(f"   หน้า Listing:  {'✅ OK' if listing_ok else '❌ BROKEN'}")
    if not listing_ok:
        all_ok = False

    if detail_result:
        detail_ok = detail_result["working"]
        print(f"   หน้า Detail:   {'✅ OK' if detail_ok else '❌ BROKEN'}")
        if not detail_ok:
            all_ok = False

    if all_ok:
        print(f"\n🎉 ทุกอย่างปกติ! Scraper พร้อมใช้งาน")
    else:
        print(f"\n🚨 พบปัญหา! JobsDB อาจเปลี่ยน HTML structure")
        print(f"   → ต้องอัพเดท selector ใน scrape_jobsdb.py / scrape_jobsdb_details.py")

    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(run_health_check())
