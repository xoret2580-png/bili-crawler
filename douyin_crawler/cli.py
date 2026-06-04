"""CLI入口 — 抖音视频逐字稿提取"""
import argparse, json, sys, signal
from . import asr

class TimeoutError(Exception): pass
def _handler(s, f): raise TimeoutError()

def process(video_id, get_comments=False):
    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(300)
    try:
        audio = asr.download_audio(video_id)
        if not audio:
            return json.dumps({"error":"download failed"}, ensure_ascii=False)
        lines = asr.transcribe(audio)
        asr.cleanup(audio)
        comments = None
        if get_comments:
            from . import comments as cm
            comments = cm.extract(video_id)
        signal.alarm(0)
        d = {"video_id":video_id, "source":"asr", "lines":len(lines), "chars":sum(len(l)for l in lines), "transcript":chr(10).join(lines)}
        if comments is not None: d["comments"] = comments
        return json.dumps(d, ensure_ascii=False, indent=2)
    except TimeoutError:
        signal.alarm(0)
        return json.dumps({"video_id":video_id, "error":"超时"}, ensure_ascii=False)
    except Exception as e:
        signal.alarm(0)
        return json.dumps({"video_id":video_id, "error":str(e)}, ensure_ascii=False)

def main():
    p = argparse.ArgumentParser(description="douyin-crawler — 抖音视频逐字稿提取")
    p.add_argument("video_id", help="抖音视频ID")
    p.add_argument("--comments", action="store_true", help="提取评论(需Playwright)")
    p.add_argument("-o", "--output")
    a = p.parse_args()
    result = process(a.video_id, a.comments)
    if a.output:
        with open(a.output,"w",encoding="utf-8") as f: f.write(result)
    else: print(result)

if __name__ == "__main__": main()
