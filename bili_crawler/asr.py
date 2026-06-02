"""ASR降级层 — yt-dlp下载音频 + Whisper转写"""
import subprocess, os, tempfile
def download_audio(bvid, output_dir=None):
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    out_tpl = os.path.join(output_dir, bvid + ".%(ext)s")
    cmd = ["yt-dlp", "-f", "bestaudio",
        "--add-header", "User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "--add-header", "Referer:https://www.bilibili.com/",
        "-o", out_tpl, "https://www.bilibili.com/video/" + bvid]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    for f in os.listdir(output_dir):
        if f.startswith(bvid):
            return os.path.join(output_dir, f)
    return None
def transcribe(audio_path, model_size="tiny", language="zh"):
    import whisper
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, language=language)
    return [seg["text"].strip() for seg in result.get("segments",[]) if seg.get("text","").strip()]
def cleanup(audio_path):
    try:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
    except:
        pass
