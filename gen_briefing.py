import json, urllib.request, datetime, html, os, base64

# ===================== 可配置项（按需修改） =====================
WX_APPID = "wx21780df9676cf9f7" # 公众号【开发者ID(AppID)】（用户提供，wx 开头，JS-SDK 用）。注意：JS-SDK 实际生效
                                  # 还需后端用 AppSecret 计算 signature 注入 wx.config；且分享域名须已在公众号后台
                                  # 「JS接口安全域名」中备案（raw github.io 不满足）。缺这两样则网页可看、可手动「…」分享。
SHARE_IMG_URL = ""              # 分享缩略图绝对地址(HTTPS)，留空则用内置 logo 兜底
SHARE_TITLE = "AI HOT 每日简报"
SHARE_DESC = "每天 AI 圈最值得看的大事，按五大版块精排"
# ==============================================================

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
BASE = "https://aihot.virxact.com/api/public/items"

now = datetime.datetime.now(datetime.timezone.utc)
since_dt = now - datetime.timedelta(hours=24)
since = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

url = f"{BASE}?mode=selected&since={since}&take=50"
req = urllib.request.Request(url, headers={"User-Agent": UA})
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(r.read().decode("utf-8"))

items = data.get("items", [])
raw_count = data.get("count", len(items))
# 精炼：按 score 取前 10 条，避免读者信息过载
items.sort(key=lambda x: (x.get("score") or 0), reverse=True)
items = items[:10]
total = len(items)

CATEGORY_META = {
    "ai-models":  ("模型发布 / 更新", "#6366f1"),
    "ai-products": ("产品发布 / 更新", "#10b981"),
    "industry":    ("行业动态",       "#f59e0b"),
    "paper":       ("论文研究",       "#ec4899"),
    "tip":         ("技巧与观点",     "#06b6d4"),
}
ORDER = ["ai-models", "ai-products", "industry", "paper", "tip"]

def beijing_time(iso):
    if not iso:
        return None
    dt = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.astimezone(datetime.timezone(datetime.timedelta(hours=8)))

def human_time(iso):
    dt_bj = beijing_time(iso)
    if dt_bj is None:
        return ""
    now_bj = now.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
    diff = now_bj - dt_bj
    mins = int(diff.total_seconds() // 60)
    rel = "刚刚" if mins < 1 else (f"{mins} 分钟前" if mins < 60 else (f"{mins // 60} 小时前" if mins < 1440 else f"{mins // 1440} 天前"))
    return f"今天 {dt_bj.strftime('%H:%M')} · {rel}" if dt_bj.date() == now_bj.date() else f"{dt_bj.month}/{dt_bj.day} {dt_bj.strftime('%H:%M')} · {rel}"

grouped = {k: [] for k in ORDER}
for it in items:
    cat = it.get("category")
    if cat in grouped:
        grouped[cat].append(it)

all_sorted = sorted(items, key=lambda x: x.get("publishedAt") or "", reverse=True)
global_index = {it["id"]: i for i, it in enumerate(all_sorted, 1)}

DATE_LABEL = now.astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d")
SINCE_LABEL = since_dt.astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime("%m-%d %H:%M")
NOW_LABEL = now.astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime("%m-%d %H:%M")

# 内置兜底 logo（data URI），保证分享卡片有缩略图可抓
LOGO_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6366f1"/><stop offset="1" stop-color="#ec4899"/></linearGradient></defs><rect width="200" height="200" rx="40" fill="url(#g)"/><text x="100" y="118" font-size="64" font-family="sans-serif" font-weight="800" fill="#fff" text-anchor="middle">AI</text></svg>'
LOGO_DATAURI = "data:image/svg+xml;base64," + base64.b64encode(LOGO_SVG.encode()).decode()

cards_html = ""
for cat in ORDER:
    clist = grouped[cat]
    if not clist:
        continue
    label, color = CATEGORY_META[cat]
    clist_sorted = sorted(clist, key=lambda x: x.get("publishedAt") or "", reverse=True)
    cards_html += f'<section class="section">\n'
    cards_html += f'  <h2 class="section-title" style="--c:{color}"><span class="dot" style="background:{color}"></span>{label}<span class="count">{len(clist_sorted)}</span></h2>\n'
    cards_html += '  <div class="grid">\n'
    for it in clist_sorted:
        gidx = global_index[it["id"]]
        title = html.escape(it.get("title") or "")
        link = html.escape(it.get("url") or "#")
        source = html.escape(it.get("source") or "")
        summary = html.escape(it.get("summary") or "")
        tstr = human_time(it.get("publishedAt"))
        cards_html += f'''    <article class="card" style="--c:{color}">
      <span class="num">{gidx}</span>
      <a class="card-title" href="{link}" target="_blank" rel="noopener">{title}</a>
      <div class="meta"><span class="src">{source}</span><span class="time">{tstr}</span></div>
      <p class="summary">{summary}</p>
    </article>
'''
    cards_html += '  </div>\n</section>\n'

og_img = SHARE_IMG_URL if SHARE_IMG_URL else LOGO_DATAURI

TPL = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<meta property="og:title" content="__OG_TITLE__">
<meta property="og:description" content="__OG_DESC__">
<meta property="og:image" content="__OG_IMG__">
<meta property="og:type" content="website">
<meta name="description" content="__OG_DESC__">
<script src="https://res.wx.qq.com/open/js/jweixin-1.6.0.js"></script>
<script>
// 公众号分享到朋友圈：需后端用 AppSecret 计算 signature 后注入下方 config
// 文档：https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/JS-SDK.html
wx.config({
  debug:false,
  appId:'__WX_APPID__',
  timestamp:0, nonceStr:'', signature:'',
  jsApiList:['updateTimelineShareData','updateAppMessageShareData']
});
wx.ready(function(){
  var shareImg = '__OG_IMG__';
  wx.updateTimelineShareData({ title: document.title, link: location.href, imgUrl: shareImg });
  wx.updateAppMessageShareData({ title: document.title, desc: '__OG_DESC__', link: location.href, imgUrl: shareImg });
});
</script>
<style>
  :root { --indigo:#6366f1; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    background:linear-gradient(160deg,#0f172a 0%,#1e1b4b 55%,#0f172a 100%); color:#e2e8f0; line-height:1.6; padding:32px 16px 64px; }
  @media (prefers-color-scheme: light) {
    body { background:linear-gradient(160deg,#eef2ff 0%,#faf5ff 55%,#eef2ff 100%); color:#1e293b; }
    .card { background:#ffffff; box-shadow:0 1px 3px rgba(15,23,42,.08),0 8px 24px rgba(99,102,241,.06); }
    .card-title { color:#1e293b; } .card-title:hover { color:var(--indigo); }
    .summary { color:#475569; } .src,.time,.subtitle { color:#64748b; } header h1 { color:#1e293b; }
  }
  .wrap { max-width:960px; margin:0 auto; }
  header { text-align:center; margin-bottom:32px; }
  header h1 { font-size:30px; font-weight:800; letter-spacing:.5px;
    background:linear-gradient(90deg,#818cf8,#c084fc,#f472b6); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
  .subtitle { font-size:14px; opacity:.85; margin-top:8px; }
  .section { margin:28px 0; }
  .section-title { font-size:18px; font-weight:700; display:flex; align-items:center; gap:10px; margin-bottom:14px; }
  .section-title .dot { width:10px; height:10px; border-radius:50%; display:inline-block; }
  .section-title .count { font-size:12px; background:rgba(99,102,241,.18); color:#a5b4fc; padding:2px 9px; border-radius:20px; font-weight:600; }
  .grid { display:grid; gap:14px; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); }
  .card { position:relative; background:rgba(30,41,59,.72); border:1px solid rgba(148,163,184,.16);
    border-left:3px solid var(--c); border-radius:12px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,.25); transition:transform .15s ease,box-shadow .15s ease; }
  .card:hover { transform:translateY(-3px); box-shadow:0 10px 30px rgba(99,102,241,.25); }
  .num { position:absolute; top:12px; right:14px; font-size:12px; font-weight:700; color:var(--c); opacity:.65; }
  .card-title { display:block; font-size:15px; font-weight:700; color:#f1f5f9; text-decoration:none; margin-bottom:8px; padding-right:28px; }
  .card-title:hover { color:#a5b4fc; }
  .meta { display:flex; justify-content:space-between; font-size:12px; margin-bottom:8px; gap:8px; }
  .src { color:#94a3b8; } .time { color:#94a3b8; white-space:nowrap; }
  .summary { font-size:13px; color:#cbd5e1; }
  footer { text-align:center; font-size:12px; opacity:.7; margin-top:40px; }
</style>
</head>
<body>
<img src="__OG_IMG__" style="display:none" alt="">
<div class="wrap">
  <header>
    <h1>AI HOT 简报 · __DATE__</h1>
    <p class="subtitle">时间窗 __SINCE__ ~ __NOW__（北京时间） · 候选 __RAW__ 条 · 精选 __TOTAL__ 条 · 按发布时间倒序</p>
  </header>
__CARDS__
  <footer>数据来自 aihot.virxact.com · 由数字生命卡兹克整理</footer>
</div>
</body>
</html>'''

html_doc = (TPL
    .replace("__TITLE__", f"AI HOT 简报 · {DATE_LABEL}")
    .replace("__OG_TITLE__", SHARE_TITLE)
    .replace("__OG_DESC__", SHARE_DESC)
    .replace("__OG_IMG__", og_img)
    .replace("__WX_APPID__", WX_APPID)
    .replace("__DATE__", DATE_LABEL)
    .replace("__SINCE__", SINCE_LABEL)
    .replace("__NOW__", NOW_LABEL)
    .replace("__TOTAL__", str(total))
    .replace("__RAW__", str(raw_count))
    .replace("__CARDS__", cards_html))

out_dir = os.path.dirname(os.path.abspath(__file__))
dated_path = os.path.join(out_dir, f"ai-hot-briefing-{DATE_LABEL}.html")
index_path = os.path.join(out_dir, "index.html")
with open(dated_path, "w", encoding="utf-8") as f:
    f.write(html_doc)
with open(index_path, "w", encoding="utf-8") as f:
    f.write(html_doc)
print("WROTE", dated_path)
print("WROTE", index_path)
print("items:", total)
