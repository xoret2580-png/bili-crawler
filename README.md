# bili-crawler

B站视频逐字稿提取工具。**默认走音频转写（ASR）**，不依赖AI字幕API。

作者：茶修
GitHub：https://github.com/xoret2580-png/bili-crawler

## 原理

直接下载视频音频 → 本地Whisper转写文字。整个过程零token消耗。

```
yt-dlp 下载音频 → Whisper 语音转写 → 输出逐字稿
                                              ↓
                             可选：Playwright 提取评论
```

## 安装

```bash
# 基础
pip install -e /Users/apple/Documents/bili-crawler

# ASR 依赖
pip install openai-whisper
brew install yt-dlp ffmpeg

# 评论（可选）
pip install playwright
python3 -m playwright install chromium
```

## 用法

```bash
# 单视频（核心用法：下载音频→转写）
python -m bili_crawler.cli BV1Ajf5YvEFN

# 加评论
python -m bili_crawler.cli BV1Ajf5YvEFN --comments

# 搜索前5条
python -m bili_crawler.cli "扫地机器人" --top 5

# 保存到文件
python -m bili_crawler.cli BV1Ajf5YvEFN -o result.json
```

## 输出

```json
{
  "bvid": "BV1Ajf5YvEFN",
  "title": "视频标题",
  "views": 40855,
  "source": "asr",
  "lines": 191,
  "chars": 2554,
  "subtitle": "逐字稿全文..."
}
```

## 项目结构

```
bili-crawler/
├── bili_crawler/
│   ├── __init__.py
│   ├── cli.py       入口
│   ├── api.py       B站API（搜索、视频信息）
│   ├── asr.py       音频下载+转写（核心）
│   └── comments.py  评论提取（可选）
├── README.md
└── pyproject.toml
```
