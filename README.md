# bili-crawler

B站视频逐字稿提取工具。API 优先取 AI 字幕，无字幕时降级到本地语音转写。

**作者：** 茶修

---

## 原理：为什么不耗 token

传统做法是让 AI 操控浏览器——截图、分析、点按钮，每一步都耗 token，还容易抽卡。

**这个项目反过来：AI 只负责写爬虫逻辑，爬虫本身用脚本跑，不经过 AI。**

```
curl 调 B站 API → 拿 JSON → 提取字幕（零 token）
              ↓
无字幕时 yt-dlp 下载音频 → Whisper 本地转写（零 token）
              ↓
需评论时 Playwright 打开页面 → JS 提取（零 token）
```

只有"你说话 → AI 理解你要干什么"这一步耗 token。爬虫跑的时候是纯脚本执行。

---

## 安装

```bash
# 基础功能（搜索、视频信息、AI字幕）
pip install requests

# ASR 降级（可选，无字幕视频转写用）
pip install openai-whisper
brew install yt-dlp ffmpeg

# 评论提取（可选）
pip install playwright
playwright install chromium
```

## 用法

### 基础功能（不需要额外安装）

```bash
# 拿字幕（有AI字幕直接取，零token）
python -m bili_crawler.cli BV1Ajf5YvEFN

# 输出纯文本而不是JSON
python -m bili_crawler.cli BV1Ajf5YvEFN --format txt

# 搜索关键词，拿前5条
python -m bili_crawler.cli "扫地机器人" --top 5

# 支持完整URL
python -m bili_crawler.cli https://www.bilibili.com/video/BV1Ajf5YvEFN

# 保存到文件
python -m bili_crawler.cli BV1Ajf5YvEFN -o result.json
```

### 无字幕视频（需安装 extra 依赖）

没有 AI 字幕的视频会自动走音频转写：
```bash
pip install openai-whisper
brew install yt-dlp ffmpeg

python -m bili_crawler.cli BV1xxx --asr
```

### 评论区（需安装 Playwright）

B站评论区没有公开 API，只能通过浏览器打开页面、滚动加载、从网页中提取。

```bash
pip install playwright
playwright install chromium

python -m bili_crawler.cli BV1xxx --comments
```

命令行加上 `--comments` 后，程序会自动打开浏览器（后台无窗口），进入视频页滚动到底，等评论加载完成后提取文本，然后关闭浏览器。

输出 JSON 里会多一个 `comments` 字段：
```json
{
  "bvid": "BV1xxx",
  "title": "视频标题",
  "subtitle": "逐字稿...",
  "comments": [
    {"name": "用户A", "content": "评论内容", "likes": "123"},
    {"name": "用户B", "content": "评论内容", "likes": "45"}
  ]
}
```

注意：Playwright 会打开一个隐藏的浏览器窗口。第一次运行可能需要登录 B站（弹出登录页面），登录一次后后续不需要重复登录。

## 三层降级策略

| 优先级 | 方案 | 依赖 | 速度 |
|--------|------|------|------|
| 1 | B站 API 取 AI 字幕 | curl | 秒级 |
| 2 | yt-dlp + Whisper ASR | yt-dlp, ffmpeg, openai-whisper | 分钟级 |
| 3 | Playwright 浏览器提取评论 | playwright | 取决于页面加载 |

## 输出格式

```json
{
  "bvid": "BV1Ajf5YvEFN",
  "title": "腾讯混元3D2.0开源，详细测评",
  "views": 40855,
  "source": "ai_subtitle",
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
│   ├── api.py       B站 API 调用（搜索、字幕）
│   ├── cli.py       CLI 入口
│   ├── comments.py  浏览器 DOM 提取评论
│   └── asr.py       音频转写（yt-dlp + Whisper）
├── pyproject.toml
├── README.md
└── .gitignore
```

## License

MIT
