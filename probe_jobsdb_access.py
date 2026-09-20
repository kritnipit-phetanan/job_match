"""
Probe — ทดสอบว่าเข้าถึงเนื้อหา JobsDB จาก IP ที่รันอยู่ได้ด้วยวิธีไหนบ้าง

อ่านอย่างเดียว: ไม่ต่อ database, ไม่ใช้ secret, ไม่แตะ pipeline จริง
รัน: python probe_jobsdb_access.py
"""
import sys

SEARCH_URL = "https://th.jobsdb.com/ai-engineer-jobs"
DETAIL_URL = "https://th.jobsdb.com/job/94700583"

CARD_MARKERS = ['data-card-type="JobCard"', "data-search-sol-meta"]
JD_MARKER = "jobAdDetails"
BLOCK_MARKERS = [
    "challenges.cloudflare.com",
    "ตรวจสอบความปลอดภัย",
    "Just a moment",
    "Attention Required",
    "cf-chl-",
]

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/143.0.7449.68 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}

results = {}


def summarize(label, html, status):
    cards = sum(html.count(m) for m in CARD_MARKERS)
    jd = html.count(JD_MARKER)
    blocked = [m for m in BLOCK_MARKERS if m in html]
    ok = (cards > 0 or jd > 0) and not blocked
    print(f"    status={status}  len={len(html)}  cards={cards}  jd={jd}")
    if blocked:
        print(f"    🛡️ เจอร่องรอย Cloudflare challenge: {blocked}")
    print(f"    {'✅ ผ่าน' if ok else '❌ ไม่ผ่าน'}")
    return ok


def probe_requests():
    print("\n[1] requests ธรรมดา")
    import requests

    ok_all = True
    for name, url, in (("search", SEARCH_URL), ("detail", DETAIL_URL)):
        r = requests.get(url, headers=HEADERS, timeout=30)
        print(f"  {name}: {url}")
        ok_all &= summarize(name, r.text, r.status_code)
    return ok_all


def probe_curl_cffi():
    print("\n[2] curl_cffi (ปลอม TLS/JA3 เป็น Chrome แท้)")
    from curl_cffi import requests as cffi_requests

    ok_all = True
    for name, url in (("search", SEARCH_URL), ("detail", DETAIL_URL)):
        r = cffi_requests.get(url, impersonate="chrome", timeout=30)
        print(f"  {name}: {url}")
        ok_all &= summarize(name, r.text, r.status_code)
    return ok_all


def probe_playwright_chrome():
    print("\n[3] Playwright + Chrome จริง (channel='chrome')")
    from playwright.sync_api import sync_playwright

    ok_all = True
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            user_agent=UA, viewport={"width": 1280, "height": 800}, locale="th-TH"
        )
        page = context.new_page()
        for name, url in (("search", SEARCH_URL), ("detail", DETAIL_URL)):
            page.goto(url, timeout=60000)
            page.wait_for_timeout(8000)
            print(f"  {name}: {url}")
            ok_all &= summarize(name, page.content(), "n/a")
        browser.close()
    return ok_all


def show_egress_ip():
    try:
        import requests

        r = requests.get("https://ipinfo.io/json", timeout=15)
        d = r.json()
        print(f"🌐 egress IP: {d.get('ip')}  org={d.get('org')}  region={d.get('region')}")
    except Exception as e:
        print(f"🌐 หา egress IP ไม่ได้: {e}")


if __name__ == "__main__":
    show_egress_ip()

    for label, fn in (
        ("requests", probe_requests),
        ("curl_cffi", probe_curl_cffi),
        ("playwright-chrome", probe_playwright_chrome),
    ):
        try:
            results[label] = fn()
        except Exception as e:
            print(f"  💥 {label} พังระหว่างรัน: {type(e).__name__}: {e}")
            results[label] = False

    print(f"\n{'='*55}")
    print("สรุปผล (จาก IP ที่รัน probe นี้)")
    print(f"{'='*55}")
    for label, ok in results.items():
        print(f"  {'✅' if ok else '❌'}  {label}")
    print(f"{'='*55}")

    if not any(results.values()):
        print("👉 ไม่ผ่านสักวิธี — แปลว่าโดนบล็อกที่ระดับ IP ต้องย้ายไปรันจาก IP อื่น")
    else:
        winners = [k for k, v in results.items() if v]
        print(f"👉 ใช้ได้: {winners} — เขียน scraper ใหม่ด้วยวิธีนี้ได้เลย")
