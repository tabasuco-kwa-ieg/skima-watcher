import re, os, requests, bs4, shelve, pathlib
from datetime import datetime, timedelta

SELLER_ID = "151777"                      # ←監視したい出品者のID
BASE_URL  = f"https://skima.jp/profile/dl_products?id={SELLER_ID}"
IFTTT_KEY = os.getenv("IFTTT_KEY")        # GitHub Secrets から取得
IFTTT_URL = f"https://maker.ifttt.com/trigger/skima_opt_new/with/key/{IFTTT_KEY}"
KEEP_DAYS = 30
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

# .github/actions/cache に保存すると GitHub Actions 側で永続化しやすい
CACHE     = pathlib.Path(".cache")
CACHE.mkdir(exist_ok=True)
DB_PATH   = str(CACHE / "items.db")

def scrape_item(iid: str) -> tuple[str, str]:
    """商品タイトルとサムネ URL を返す。取れなければプレースホルダを返す"""
    url = f"https://skima.jp/dl/detail?id={iid}"
    r   = requests.get(url, headers=UA, timeout=10)
    if r.status_code != 200:
        print("skip", iid, r.status_code)
        return f"商品 {iid}", ""

    soup = bs4.BeautifulSoup(r.text, "html.parser")

    # --- タイトル ---
    if meta := soup.select_one('meta[property="og:title"]'):
        title = meta["content"]
    elif h1 := soup.select_one("h1"):
        title = h1.get_text(strip=True)
    else:
        title = f"商品 {iid}"

    # --- サムネ ---
    thumb = ""
    if img := soup.select_one('meta[property="og:image"]'):
        thumb = img["content"]

    return title, thumb

with shelve.open(DB_PATH) as db:
    prev = db.get("items", {})

    html = requests.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"}).text

    soup  = bs4.BeautifulSoup(html, "html.parser")
    selector = 'a[href^="/dl/detail"]'           # 汎用化
    items = set()
    
    for a in soup.select(selector):
        m = re.search(r'\d+', a['href'])
        if m:
            items.add(m.group())
    
    print("取得:", len(items), "件", list(items)[:5])
    
    new = [iid for iid in items if iid not in prev]
    print("新規:", new)
    
    for iid in new:
        title, thumb = scrape_item(iid)
        payload = {
            "username": "SKIMA Watcher",
            "embeds": [{
                "title": title,
                "url": f"https://skima.jp/dl/detail?id={iid}",
                "thumbnail": {"url": thumb},
                "color": 0xFFCC00,                      # 好きな16進 → 10進で渡す
                "footer": {"text": "opt販売 / 自動通知"}
            }]
        }
        maker_json = {"value1": json.dumps(payload)}
        requests.post(IFTTT_URL, json=maker_json).raise_for_status()

    # --- 古い ID を整理 ---
    now = datetime.utcnow().isoformat()
    for iid in items:
        prev.setdefault(iid, now)

    cutoff = datetime.utcnow() - timedelta(days=KEEP_DAYS)
    prev = {iid: ts for iid, ts in prev.items()
            if datetime.fromisoformat(ts) > cutoff}

    db["items"] = prev
