"""bili-crawler: B站视频逐字稿提取工具"""
import argparse, json, sys
from . import api, asr
VERSION = "1.0.0"

def output_json(info, lines, src, comments=None):
    d = {"bvid":info["bvid"],"title":info["title"],"views":info["views"],
         "source":src,"lines":len(lines),"chars":sum(len(l)for l in lines),
         "subtitle":chr(10).join(lines)}
    if comments is not None:
        d["comments"] = comments
    return json.dumps(d, ensure_ascii=False, indent=2)

def process(bvid, get_comments=False):
    info = api.video_info(bvid)
    if info is None:
        return json.dumps({"error":"video not found"},ensure_ascii=False)
    lines, src = [], "none"
    try:
        url = api.subtitle_url(info["aid"], info["cid"])
        if url:
            lines = api.download_subtitle(url)
            if lines:
                src = "ai_subtitle"
    except:
        pass
    if not lines:
        audio = asr.download_audio(bvid)
        if audio:
            lines = asr.transcribe(audio)
            if lines:
                src = "asr"
            asr.cleanup(audio)
    comments = None
    if get_comments:
        try:
            from . import comments as cm
            comments = cm.extract(bvid)
        except Exception as e:
            print("comments:", e, file=sys.stderr)
            comments = []
    return output_json(info, lines, src, comments)

def search_and_process(keyword, top=5, get_comments=False):
    results = api.search(keyword)
    if not results:
        return json.dumps({"error":"no results"},ensure_ascii=False)
    out = []
    for v in results[:top]:
        w = str(round(v["views"]/10000,1))
        print("[" + w + "w] " + v["title"][:40] + "...", file=sys.stderr)
        out.append(json.loads(process(v["bvid"], get_comments)))
    return json.dumps(out, ensure_ascii=False, indent=2)

def main():
    p = argparse.ArgumentParser(description="bili-crawler v"+VERSION)
    p.add_argument("input", help="BVID/URL/关键词")
    p.add_argument("--top", type=int, default=0)
    p.add_argument("--comments", action="store_true")
    p.add_argument("-o", "--output")
    a = p.parse_args()
    raw = a.input.strip()
    for pfx in ["https://www.bilibili.com/video/","http://www.bilibili.com/video/","https://b23.tv/"]:
        if raw.startswith(pfx):
            raw = raw[len(pfx):].split("?")[0].split("/")[0]
    if a.top > 0:
        result = search_and_process(raw, a.top, a.comments)
    else:
        result = process(raw, a.comments)
    if a.output:
        with open(a.output,"w",encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)

if __name__ == "__main__":
    main()