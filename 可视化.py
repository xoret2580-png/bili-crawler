import streamlit as st
import json
import os
import re
import glob
import jieba
import matplotlib.pyplot as plt
from collections import Counter
from pyecharts.charts import Map
from pyecharts import options as opts
from streamlit_echarts import st_pyecharts

plt.rcParams["font.family"] = ["PingFang HK", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="知乎评论可视化", layout="wide")
st.title("📊 知乎评论区可视化分析")

# ---------- 自动扫描 jsonl ----------
data_root = os.path.expanduser("~/Documents/Reasonix/爬虫/data/")
zhihu_dir = os.path.join(data_root, "zhihu")

all_files = []
if os.path.exists(zhihu_dir):
    for f in glob.glob(os.path.join(zhihu_dir, "**/*.jsonl"), recursive=True):
        all_files.append(f)
    for f in glob.glob(os.path.join(zhihu_dir, "*.jsonl")):
        all_files.append(f)
all_files = list(set(all_files))
all_files.sort(key=os.path.getmtime, reverse=True)

if not all_files:
    st.warning("⚠ data/zhihu/ 下没有 jsonl 文件")
    st.stop()

file_path = st.selectbox("选择数据文件", all_files,
    format_func=lambda x: os.path.relpath(x, os.path.expanduser("~")))

# ---------- 读取 ----------
comments = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            comments.append(json.loads(line))
st.success(f"✅ 共 {len(comments)} 条评论")

# ---------- 提取 ----------
ip_locations = []
all_text = ""
for c in comments:
    ip = c.get("ip_location", "")
    if ip:
        for s in ["省","市","自治区","特别行政区","壮族","回族","维吾尔"]:
            ip = ip.replace(s, "")
        ip_locations.append(ip)
    content = c.get("content", "")
    if content:
        all_text += content + "\n"

# ---------- 1. 地图（去掉 map_echarts 改用纯 pyecharts 输出 HTML）----------
if ip_locations:
    st.subheader("🗺️ 评论 IP 属地分布")
    ip_counter = Counter(ip_locations)
    ip_data = [(k, v) for k, v in ip_counter.items()]

    # pyecharts 直接输出为 HTML 内嵌
    from pyecharts.charts import Map as PyMap
    c = PyMap()
    c.add("评论数", ip_data, "china", is_map_symbol_show=False)
    c.set_global_opts(
        visualmap_opts=opts.VisualMapOpts(max_=max(v for _, v in ip_data)),
        title_opts=opts.TitleOpts(title="")
    )
    st.components.v1.html(c.render_embed(), height=500)
else:
    st.info("ℹ 无 IP 属地数据")

# ---------- 2. 词频 TOP20 ----------
st.subheader("🏆 高频词 TOP 20")
words = jieba.lcut(all_text)
words = [w for w in words if len(w) >= 2 and not re.match(r'^\W+$', w)]
word_freq = Counter(words).most_common(20)

for idx, (word, num) in enumerate(word_freq, 1):
    st.markdown(f"{idx:02d}. **{word}** — {num} 次")

# ---------- 3. 词云 ----------
st.subheader("☁️ 评论关键词词云")
if word_freq:
    from wordcloud import WordCloud

    # 自动检测 Mac 可用中文字体
    font_candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    font_path = None
    for fp in font_candidates:
        if os.path.exists(fp):
            font_path = fp
            break

    if font_path:
        wc = WordCloud(
            font_path=font_path,
            width=1000, height=600,
            background_color="white",
            max_words=100
        )
        wc.generate_from_frequencies(dict(word_freq))
        fig, ax = plt.subplots(figsize=(12, 7))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
    else:
        st.warning("⚠ 未找到中文字体，词云无法生成")
else:
    st.info("ℹ 无文本内容")
