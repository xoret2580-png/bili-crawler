"""B站 API 调用层 — 搜索、视频信息"""
import json, subprocess, urllib.parse, time

_last_call = 0.0
MIN_INTERVAL = 5.0
MAX_RETRIES = 3

def _req(url, timeout=15):
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    _last_call = time.time()

    for attempt in range(MAX_RETRIES):
        cmd = ["curl", "-s", url,
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "-H", "Referer: https://www.bilibili.com/",
            "-H", "Cookie: sid=50qwx6pr"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.stdout.strip():
            try:
                return json.loads(r.stdout)
            except json.JSONDecodeError:
                pass
        if attempt < MAX_RETRIES - 1:
            time.sleep(3)
    return {"code": -1, "message": "request failed"}

def search(keyword, order="click", page=1):
    kw = urllib.parse.quote(keyword)
    data = _req(f"https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={kw}&order={order}&page={page}")
    results = data.get("data", {}).get("result", [])
    out = []
    for v in results:
        t = v.get("title", "").replace('<em class="keyword">', "").replace("</em>", "")
        out.append({"bvid": v.get("bvid",""), "title": t, "views": v.get("play",0), "author": v.get("author","")})
    return out

def video_info(bvid):
    data = _req(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}")
    if "data" not in data:
        return None
    d = data["data"]
    return {"bvid": bvid, "aid": d["aid"], "cid": d["cid"], "title": d["title"],
            "views": d.get("stat",{}).get("view",0), "duration": d.get("duration",0)}
