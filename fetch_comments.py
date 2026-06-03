"""
Fetch all comments for the 9 Bilibili videos using the reply API.
Outputs structured JSON with comment text + likes for analysis.
"""
import sys, json, time, os

# Add the bili-crawler directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bili_crawler import api

BVS = [
    ("BV1sy41187tQ", "买前必备！八款对比"),
    ("BV11SdUYFEnS", "2025年九款最新旗舰扫地机真实横评"),
    ("BV13RxWeyEMy", "某音上的扫地机器人测评，到底有多假？"),
    ("BV1he4y1f7u3", "家有14只猫，一台扫拖机器人够用吗"),
    ("BV16M4m1C713", "灵魂拷问：你是什么垃圾"),
    ("BV19v41137sT", "拼夕夕10块钱的扫地机器人真的能用吗"),
    ("BV1c84y1B7eC", "竟被扫地机器人查岗了"),
    ("BV1St41187E7", "云鲸J5测评"),
    ("BV1ZKVd6XErn", "2026年扫地机器人选购终极指南"),
]

def fetch_replies(oid, page=1, max_pages=50):
    """Fetch replies using the bilibili reply API via curl"""
    all_replies = []
    total_count = None
    
    for pn in range(1, max_pages + 1):
        url = f"https://api.bilibili.com/x/v2/reply?type=1&oid={oid}&sort=2&pn={pn}"
        data = api._req(url)
        
        if data.get("code") != 0:
            print(f"  API error on page {pn}: {data.get('message', 'unknown')}", file=sys.stderr)
            break
        
        page_data = data.get("data", {})
        page_info = page_data.get("page", {})
        if total_count is None:
            total_count = page_info.get("count", 0)
            print(f"  Total comments: {total_count}", file=sys.stderr)
        
        replies = page_data.get("replies", [])
        if not replies:
            print(f"  No more replies at page {pn}", file=sys.stderr)
            break
        
        for r in replies:
            content = r.get("content", {}).get("message", "")
            all_replies.append({
                "rpid": r.get("rpid_str", ""),
                "user": r.get("member", {}).get("uname", ""),
                "content": content[:1000],  # cap length
                "likes": r.get("like", 0),
                "ctime": r.get("ctime", 0),
                "replies_count": r.get("rcount", 0),
            })
        
        print(f"  Page {pn}: {len(replies)} replies fetched (total so far: {len(all_replies)})", file=sys.stderr)
        
        # If we got fewer than 20 per page, we're done
        if len(replies) < 20:
            break
        
        # Rate limit
        time.sleep(0.5)
    
    return all_replies

def fetch_sub_replies(oid, root_rpid, max_pages=10):
    """Fetch sub-replies for a given root reply"""
    all_replies = []
    for pn in range(1, max_pages + 1):
        url = f"https://api.bilibili.com/x/v2/reply/reply?type=1&oid={oid}&root={root_rpid}&pn={pn}"
        data = api._req(url)
        if data.get("code") != 0:
            break
        replies = data.get("data", {}).get("replies", [])
        if not replies:
            break
        for r in replies:
            content = r.get("content", {}).get("message", "")
            all_replies.append({
                "rpid": r.get("rpid_str", ""),
                "user": r.get("member", {}).get("uname", ""),
                "content": content[:1000],
                "likes": r.get("like", 0),
                "ctime": r.get("ctime", 0),
                "is_sub": True,
            })
        if len(replies) < 20:
            break
        time.sleep(0.3)
    return all_replies

def main():
    result = {}
    
    for bvid, title in BVS:
        print(f"\n=== {bvid}: {title} ===", file=sys.stderr)
        
        # Get video info for aid
        info = api.video_info(bvid)
        if info is None:
            print(f"  ERROR: video not found", file=sys.stderr)
            result[bvid] = {"title": title, "error": "video not found", "comments": []}
            continue
        
        aid = info["aid"]
        print(f"  aid={aid}, views={info['views']}", file=sys.stderr)
        
        # Fetch top-level replies
        replies = fetch_replies(aid, max_pages=50)
        
        # Also fetch sub-replies for top-level replies with many replies
        # (limited to top 5 root replies with most replies)
        top_roots = sorted(replies, key=lambda x: x.get("replies_count", 0), reverse=True)[:5]
        for root in top_roots:
            if root.get("replies_count", 0) > 0:
                subs = fetch_sub_replies(aid, root["rpid"], max_pages=5)
                if subs:
                    print(f"  + {len(subs)} sub-replies for root {root['rpid'][:8]}...", file=sys.stderr)
                    replies.extend(subs)
        
        result[bvid] = {
            "title": title,
            "views": info["views"],
            "aid": aid,
            "total_comments": len(replies),
            "comments": replies,
        }
        
        # Be nice to the API
        time.sleep(1)
    
    # Output
    output_path = "/Users/apple/Documents/bili-crawler/all_comments.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved to {output_path}", file=sys.stderr)
    
    # Print summary
    print("\n=== Summary ===", file=sys.stderr)
    for bvid, data in result.items():
        if "error" in data:
            print(f"  {bvid}: ERROR - {data['error']}", file=sys.stderr)
        else:
            print(f"  {bvid}: {data['total_comments']} comments", file=sys.stderr)

if __name__ == "__main__":
    main()
