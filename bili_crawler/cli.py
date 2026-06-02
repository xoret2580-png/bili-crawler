# CLI entry point
import argparse, json, sys
from . import api

def output_text(lines):
    return chr(10).join(lines)

def output_json(info, lines, src, comments=None):
    d = {"bvid": info["bvid"], "title": info["title"],
         "views": info["views"], "source": src,
         "lines": len(lines), "chars": sum(len(l) for l in lines),
         "subtitle": output_text(lines)}
    if comments:
        d["comments"] = comments
    return json.dumps(d, ensure_ascii=False, indent=2)

def process_single(bvid, fmt="json", use_asr=False, get_comments=False):
    info = api.video_info(bvid)
    if info is None:
        return json.dumps({"error":"video not found"}, ensure_ascii=False)
    lines, src = [], "none"
    url = api.subtitle_url(info["aid"], info["cid"])
    if url:
        lines = api.download_subtitle(url)
        src = "ai_subtitle"
    if not lines and use_asr:
        try:
            from . import asr
            audio = asr.download_audio(bvid)
            if audio:
                lines = asr.transcribe(audio)
                src = "asr"
                asr.cleanup(audio)
        except Exception as e:
            print("ASR failed:", e, file=sys.stderr)

    comments = None
    if get_comments:
        try:
            from .comments import has_browser, extract_comments_from_page
            if not has_browser():
                print("Comments need Playwright: pip install playwright", file=sys.stderr)
            else:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto("https://www.bilibili.com/video/" + bvid, wait_until="networkidle")
                    comments = extract_comments_from_page(page)
                    browser.close()
        except ImportError:
            print("Comments need Playwright: pip install playwright", file=sys.stderr)
        except Exception as e:
            print("Comments failed:", e, file=sys.stderr)

    if fmt == "txt":
        return output_text(lines)
    return output_json(info, lines, src, comments)

def process_search(keyword, top=5, fmt="json", use_asr=False, get_comments=False):
    results = api.search(keyword)
    if not results:
        return json.dumps({"error":"no results"}, ensure_ascii=False)
    out = []
    for v in results[:top]:
        w = str(round(v["views"]/10000, 1))
        print("  [" + w + "w] " + v["title"][:40] + "...", file=sys.stderr)
        item = json.loads(process_single(v["bvid"], "json", use_asr, get_comments))
        out.append(item)
    return json.dumps(out, ensure_ascii=False, indent=2)

def main():
    p = argparse.ArgumentParser(description="Bilibili subtitle extractor")
    p.add_argument("input", help="BVID / URL / keyword")
    p.add_argument("--top", type=int, default=0, help="search mode: top N")
    p.add_argument("--format", choices=["json","txt"], default="json", help="output format")
    p.add_argument("--asr", action="store_true", help="fallback to ASR if no subtitle")
    p.add_argument("--comments", action="store_true", help="extract comments (needs Playwright)")
    p.add_argument("-o", "--output", help="output file")
    a = p.parse_args()
    raw = a.input.strip()
    for pfx in ["https://www.bilibili.com/video/", "http://www.bilibili.com/video/", "https://b23.tv/"]:
        if raw.startswith(pfx):
            raw = raw[len(pfx):].split("?")[0].split("/")[0]
    if a.top > 0:
        result = process_search(raw, a.top, a.format, a.asr, a.comments)
    else:
        result = process_single(raw, a.format, a.asr, a.comments)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)

if __name__ == "__main__":
    main()