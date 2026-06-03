import { chromium } from 'playwright';
import fs from 'fs';

const BVS = [
  ["BV1sy41187tQ", "买前必备！八款对比"],
  ["BV11SdUYFEnS", "2025年九款最新旗舰扫地机真实横评"],
  ["BV13RxWeyEMy", "某音上的扫地机器人测评，到底有多假？"],
  ["BV1he4y1f7u3", "家有14只猫，一台扫拖机器人够用吗"],
  ["BV16M4m1C713", "灵魂拷问：你是什么垃圾"],
  ["BV19v41137sT", "拼夕夕10块钱的扫地机器人真的能用吗"],
  ["BV1c84y1B7eC", "竟被扫地机器人查岗了"],
  ["BV1St41187E7", "云鲸J5测评"],
  ["BV1ZKVd6XErn", "2026年扫地机器人选购终极指南"],
];

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function extractComments(page, bvid) {
  const comments = [];
  
  // 滚动到底部加载评论，最多滚10次
  for (let i = 0; i < 10; i++) {
    // 先用 JS 提取当前可见的评论
    const items = await page.evaluate(() => {
      const replies = document.querySelectorAll('.reply-item, .comment-item, .bpx-player-video-info-panel .reply-item');
      if (replies.length === 0) {
        // 尝试其他 B站评论选择器
        const altReplies = document.querySelectorAll('[class*="reply"] [class*="content"], .reply-wrap .reply-content');
        return Array.from(altReplies).map(el => {
          const item = el.closest('[class*="reply"]') || el.parentElement;
          const nameEl = item?.querySelector('.user-name, .reply-user-name, [class*="user-name"]');
          const likeEl = item?.querySelector('.like-count, .reply-like .count, [class*="like"] [class*="count"]');
          return {
            user: nameEl?.textContent?.trim() || '',
            content: el.textContent?.trim() || '',
            likes: parseInt(likeEl?.textContent?.trim() || '0'),
          };
        });
      }
      return Array.from(replies).map(el => {
        const nameEl = el.querySelector('.user-name, .reply-user-name, [class*="user"]');
        const contentEl = el.querySelector('.reply-content, .root-reply-content, .content, [class*="content"]');
        const likeEl = el.querySelector('.like-count, .reply-like .count, [class*="like"] [class*="count"]');
        return {
          user: nameEl?.textContent?.trim() || '',
          content: contentEl?.textContent?.trim() || '',
          likes: parseInt(likeEl?.textContent?.trim() || '0'),
        };
      });
    });
    
    for (const item of items) {
      if (item.content && !comments.some(c => c.content === item.content)) {
        comments.push(item);
      }
    }
    
    console.log(`  [scroll ${i+1}] Found ${comments.length} unique comments`);
    
    // 尝试滚动
    const prevHeight = await page.evaluate('document.body.scrollHeight');
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
    await sleep(3000);
    const newHeight = await page.evaluate('document.body.scrollHeight');
    
    if (newHeight === prevHeight) {
      console.log('  No more content to load, stopping scroll');
      break;
    }
  }
  
  return comments;
}

async function main() {
  const allResults = {};
  
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox']
  });
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1920, height: 1080 },
  });
  
  const page = await context.newPage();
  
  for (const [bvid, title] of BVS) {
    console.log(`\n=== ${bvid}: ${title} ===`);
    
    try {
      const url = `https://www.bilibili.com/video/${bvid}`;
      console.log(`  Navigating to ${url}`);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      
      // 等待页面加载完成
      await sleep(5000);
      
      const comments = await extractComments(page, bvid);
      console.log(`  Total: ${comments.length} comments`);
      
      allResults[bvid] = {
        title,
        comment_count: comments.length,
        comments,
      };
    } catch (err) {
      console.error(`  Error: ${err.message}`);
      allResults[bvid] = { title, error: err.message, comments: [] };
    }
    
    // 间隔
    await sleep(2000);
  }
  
  await browser.close();
  
  // 保存 JSON
  const output = '/Users/apple/Documents/bili-crawler/all_comments.json';
  fs.writeFileSync(output, JSON.stringify(allResults, null, 2), 'utf-8');
  console.log(`\n✅ Saved to ${output}`);
  
  // 摘要
  for (const [bvid] of BVS) {
    const d = allResults[bvid];
    console.log(`  ${bvid}: ${d.comment_count} comments${d.error ? ` (ERROR: ${d.error})` : ''}`);
  }
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
