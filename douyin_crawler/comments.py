"""评论提取 — Playwright浏览器"""
import json, time

def extract(video_id):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://www.douyin.com/video/{video_id}", wait_until="networkidle")
        for _ in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
        script = """() => {
            const items = document.querySelectorAll("[class*=comment],[class*=reply]");
            const r = []; items.forEach(el => {
                const t = el.innerText?.trim();
                if (t && t.length > 5 && !t.includes("登录") && !t.includes("广告"))
                    r.push(t.substring(0,300));
            });
            return JSON.stringify([...new Set(r)].slice(0,30));
        }"""
        result = page.evaluate(script)
        browser.close()
        return json.loads(result) if result != "[]" else []
