"""Playwright 评论提取（可选）"""
import json, time

def extract(bvid):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://www.bilibili.com/video/{bvid}", wait_until="networkidle")

        for _ in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

        script = """() => {
            const items = document.querySelectorAll(".reply-item, .comment-item");
            if (items.length === 0) return "[]";
            const r = [];
            items.forEach(el => {
                const name = el.querySelector(".user-name, .reply-user-name")?.textContent?.trim() || "";
                const content = el.querySelector(".reply-content, .root-reply-content, .content")?.textContent?.trim() || "";
                const likes = el.querySelector(".like-count, .reply-like .count")?.textContent?.trim() || "0";
                if (content) r.push({name, content: content.substring(0,500), likes});
            });
            return JSON.stringify(r);
        }"""
        result = page.evaluate(script)
        browser.close()
        return json.loads(result) if result != "[]" else []
