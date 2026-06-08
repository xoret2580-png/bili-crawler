#!/usr/bin/env python3
"""
知乎评论区爬虫 v2
- 交互式参数输入
- 自动修改 MediaCrawler 配置
- 运行爬虫并实时显示日志
- 爬完后显示报错汇总
"""

import os, re, sys, subprocess, shutil
from datetime import datetime

HOME = os.path.expanduser("~")
MEDIA_CRAWLER_DIR = os.path.join(HOME, "Documents", "MediaCrawler")
CONFIG_PATH = os.path.join(MEDIA_CRAWLER_DIR, "config", "base_config.py")
OUTPUT_DIR = os.path.join(HOME, "Documents", "Reasonix", "爬虫", "data", "zhihu")


def print_banner():
    print("╔══════════════════════════════╗")
    print("║     知乎评论区爬虫 v2        ║")
    print("║   ⚠ 建议每天不超过 50 篇    ║")
    print("╚══════════════════════════════╝")
    print()


def get_input():
    keyword = input("请输入搜索关键词（多个用逗号隔开）: ").strip()
    if not keyword:
        print("❌ 关键词不能为空"); sys.exit(1)
    raw = input("爬取篇数（默认20）: ").strip()
    notes_count = int(raw) if raw else 20
    raw = input("每篇评论数（默认50）: ").strip()
    comments_count = int(raw) if raw else 50
    raw = input("是否爬二级评论？(y/n, 默认n): ").strip().lower()
    enable_sub = raw == "y"
    print(f"\n📋 关键词:{keyword} 篇数:{notes_count} 评论:{comments_count} 二级:{'是' if enable_sub else '否'}\n")
    if input("确认运行？(y/n): ").strip().lower() != "y":
        print("已取消"); sys.exit(0)
    return keyword, notes_count, comments_count, enable_sub


def modify_config(keyword, notes_count, comments_count, enable_sub):
    print("[1/3] 修改配置...")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    pairs = [
        ('PLATFORM = "',    'PLATFORM = "zhihu"'),
        ('KEYWORDS = "',    f'KEYWORDS = "{keyword}"'),
        ('CRAWLER_MAX_NOTES_COUNT = ',  f'CRAWLER_MAX_NOTES_COUNT = {notes_count}'),
        ('ENABLE_GET_COMMENTS = ',      'ENABLE_GET_COMMENTS = True'),
        ('CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = ', f'CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = {comments_count}'),
        ('ENABLE_GET_SUB_COMMENTS = ',  f'ENABLE_GET_SUB_COMMENTS = {str(enable_sub)}'),
        ('CRAWLER_MAX_SLEEP_SEC = ',    'CRAWLER_MAX_SLEEP_SEC = 5'),
        ('SAVE_DATA_OPTION = "',        'SAVE_DATA_OPTION = "jsonl"'),
    ]
    for prefix, new_line in pairs:
        content = re.sub(rf'^{re.escape(prefix)}.*$', new_line, content, flags=re.MULTILINE)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("   ✅ 完成")


def run_crawler():
    """运行爬虫，收集日志中的错误信息"""
    print("[2/3] 启动爬虫（扫码登录后自动开始）...\n")

    error_keywords = ["error", "Error", "ERROR", "failed", "Failed", "异常",
                      "403", "404", "500", "timeout", "Timeout", "超时",
                      "DataFetchError", "Forbidden", "Traceback"]

    error_lines = []
    total_lines = 0

    proc = subprocess.Popen(
        ["uv", "run", "main.py", "--platform", "zhihu", "--lt", "qrcode", "--type", "search"],
        cwd=MEDIA_CRAWLER_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1)

    for line in proc.stdout:
        print(line, end="", flush=True)
        total_lines += 1
        if any(kw in line for kw in error_keywords):
            error_lines.append(line.strip())

    proc.wait()
    success = proc.returncode == 0

    print()
    print("═════════════ 爬取报告 ═════════════")
    print(f"  总日志行数: {total_lines}")
    print(f"  疑似异常数: {len(error_lines)}")

    if error_lines:
        print()
        print("  ⚠ 异常/错误日志（按出现顺序）:")
        seen = set()
        unique_errors = []
        for line in error_lines:
            if line not in seen:
                seen.add(line)
                unique_errors.append(line)
        for e in unique_errors[:20]:
            print(f"    • {e}")
        if len(unique_errors) > 20:
            print(f"    ... 还有 {len(unique_errors) - 20} 条未显示")

    if success and not error_lines:
        print("  ✅ 无异常")
    elif not success:
        print(f"  ❌ 爬虫进程异常退出 (code={proc.returncode})")

    print("══════════════════════════════════\n")
    return success


def save_result(keyword):
    print("[3/3] 整理数据...")
    data_dir = os.path.join(MEDIA_CRAWLER_DIR, "data")
    if not os.path.isdir(data_dir):
        print("   ❌ 没找到 data/ 目录"); return
    files = [f for f in os.listdir(data_dir) if f.endswith(".jsonl")]
    if not files:
        print("   ❌ 没找到 jsonl 文件"); return
    files.sort(key=lambda f: os.path.getmtime(os.path.join(data_dir, f)), reverse=True)
    latest = os.path.join(data_dir, files[0])
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    dest = os.path.join(OUTPUT_DIR, f"{keyword.split(',')[0].strip()}_{today}.jsonl")
    shutil.copy2(latest, dest)
    print(f"   ✅ 已保存: {dest}")


if __name__ == "__main__":
    print_banner()
    keyword, notes_count, comments_count, enable_sub = get_input()
    modify_config(keyword, notes_count, comments_count, enable_sub)
    if run_crawler():
        save_result(keyword)
        print("\n✅ 全部完成！")
    else:
        print("\n❌ 爬虫异常退出，请检查上面的日志")
