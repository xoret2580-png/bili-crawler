"""bili-crawler: B站视频逐字稿提取工具"""
import argparse, json, sys
from . import api, asr

VERSION = "1.0.0"

def output_json(info, lines, comments=None):
    d = {"bvid": info["bvid"], "title": info["title"], "views": info["views"],
         "source": "asr", "lines": len(lines), "chars": sum(len(l) for l in lines),
         "subtitle": "\n".join(lines)}
    if comments is not None:
        d["comments"] = comments
    return json.dumps(d, ensure_ascii=False, indent=2)

def process(bvid, get_comments=False):
    info = api.video_info(bvid)
    if info is None:
        return json.dumps({"error": "video not found"}, ensure_ascii=False)

    # 唯一路径：下载音频 → Whisper 转写
    print(f"  → 下载音频...", file=sys.stderr)
    audio = asr.download_audio(bvid)
    if not audio:
        return json.dumps({"error": "audio download failed"}, ensure_ascii=False)

    print(f"  → 语音转写...", file=sys.stderr)
    lines = asr.transcribe(audio)
    asr.cleanup(audio)

    # 评论（可选）
    comments = None
    if get_comments:
        try:
            from . import comments as cm
            comments = cm.extract(bvid)
        except ImportError:
            print(f"  ⚠ 评论需Playwright", file=sys.stderr)
            comments = []
        except Exception as e:
            print(f"  ⚠ 评论失败: {e}", file=sys.stderr)
            comments = []

    return output_json(info, lines, comments)

def search_and_process(keyword, top=5, get_comments=False):
    results = api.search(keyword)
    if not results:
        return json.dumps({"error": "no results"}, ensure_ascii=False)
    out = []
    for v in results[:top]:
        w = round(v["views"] / 10000, 1)
        print(f"[{w}w] {v['title'][:40]}...", file=sys.stderr)
        item = json.loads(process(v["bvid"], get_comments))
        out.append(item)
    return json.dumps(out, ensure_ascii=False, indent=2)

def main():
    p = argparse.ArgumentParser(description="bili-crawler — B站视频逐字稿提取")
    p.add_argument("input", help="BVID / B站URL / 搜索关键词")
    p.add_argument("--top", type=int, default=0, help="搜索前N条")
    p.add_argument("--comments", action="store_true", help="同时提取评论区（需Playwright）")
    p.add_argument("-o", "--output", help="输出文件路径")
    a = p.parse_args()

    raw = a.input.strip()
    for pfx in ["https://www.bilibili.com/video/", "http://www.bilibili.com/video/", "https://b23.tv/"]:
        if raw.startswith(pfx):
            raw = raw[len(pfx):].split("?")[0].split("/")[0]

    if a.top > 0:
        result = search_and_process(raw, a.top, a.comments)
    else:
        result = process(raw, a.comments)

    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)

if __name__ == "__main__":
    main()
