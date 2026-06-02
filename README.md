# bili-crawler

B站视频逐字稿提取工具。API优先取AI字幕，无字幕时降级到yt-dlp+Whisper本地转写。

## 安装

```bash
pip install requests
# ASR降级需要额外安装：
pip install openai-whisper
yt-dlp  # 或 brew install yt-dlp
brew install ffmpeg  # macOS
```

## 用法

```bash
# 单视频（优先AI字幕）
python -m bili_crawler.cli BV1ar2mYVEKh

# 输出纯文本
python -m bili_crawler.cli BV1ar2mYVEKh --format txt

# 无AI字幕时自动降级到语音转写
python -m bili_crawler.cli BV1ar2mYVEKh --asr

# 搜索关键词，取前5条
python -m bili_crawler.cli "扫地机器人 测评" --top 5

# 支持B站完整URL
python -m bili_crawler.cli https://www.bilibili.com/video/BV1ar2mYVEKh

# 输出到文件
python -m bili_crawler.cli BV1ar2mYVEKh -o result.json
```

## 三层降级策略

| 优先级 | 方案 | 依赖 | 速度 |
|--------|------|------|------|
| 1 | B站API取AI字幕 | requests | 秒级 |
| 2 | yt-dlp+Whisper ASR | yt-dlp, ffmpeg, openai-whisper | 分钟级 |

## 输出格式

```json
{
  "bvid": "BV1ar2mYVEKh",
  "title": "视频标题",
  "views": 814035,
  "source": "ai_subtitle",
  "lines": 206,
  "chars": 2415,
  "subtitle": "逐字稿全文..."
}
```

## 项目结构

```
bili-crawler/
├── bili_crawler/
│   ├── __init__.py
│   ├── cli.py       # 命令行入口
│   ├── api.py       # B站API调用
│   └── asr.py       # ASR降级（可选）
├── pyproject.toml
└── README.md
```

## License

MIT

## Author

**茶修**

## Disclaimer

This project is for learning and research purposes only.
