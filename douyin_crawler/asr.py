"""ASR — yt-dlp下载音频 + Whisper转写"""
import subprocess, os, tempfile
def download_audio(video_id, output_dir=None):
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    out_tpl = os.path.join(output_dir, f"dy_{video_id}.%(ext)s")
    cmd = ["yt-dlp", "-f", "bestaudio", "-o", out_tpl, f"https://www.douyin.com/video/{video_id}"]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    for f in os.listdir(output_dir):
        if f.startswith(f"dy_{video_id}"):
            return os.path.join(output_dir, f)
    return None

def transcribe(audio_path, model_size="tiny", language="zh"):
    import whisper
    try:
        import imageio_ffmpeg
        import os as _os
        _os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
    except: pass
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, language=language)
    return [seg["text"].strip() for seg in result.get("segments",[]) if seg.get("text","").strip()]

def cleanup(audio_path):
    try:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
    except: pass
