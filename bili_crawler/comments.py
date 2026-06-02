# Browser-based comment extraction (optional, requires Playwright)
import json, time

def extract_comments_from_page(page):
    """从已加载的B站视频页提取评论"""
    # Scroll down to trigger comment loading
    for _ in range(3):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

    # Extract from DOM
    script = """
() => {
    const items = document.querySelectorAll(".reply-item, .comment-item");
    if (items.length === 0) return "[]";
    const results = [];
    items.forEach(el => {
        const name = el.querySelector(".user-name, .reply-user-name")?.textContent?.trim() || "";
        const content = el.querySelector(".reply-content, .root-reply-content, .content")?.textContent?.trim() || "";
        const likes = el.querySelector(".like-count, .reply-like .count")?.textContent?.trim() || "0";
        if (content) results.push({name, content: content.substring(0, 500), likes});
    });
    return JSON.stringify(results);
}
"""
    result = page.evaluate(script)
    if result == "[]":
        return []
    return json.loads(result)

def has_browser():
    """检查是否有可用的Playwright"""
    try:
        import playwright
        return True
    except ImportError:
        return False