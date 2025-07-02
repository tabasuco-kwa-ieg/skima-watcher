import json, re, os, requests, bs4, shelve, pathlib
from datetime import datetime, timedelta

SELLERS = [
    ("151777", "skima_opt_new_yuki"),
    ("412145", "skima_opt_new_upacha"),
]
IFTTT_KEY = os.getenv("IFTTT_KEY")          # 1 つで共通

CACHE = pathlib.Path(".cache"); CACHE.mkdir(exist_ok=True)
DB_PATH = str(CACHE / "items.db")
UA = {"User-Agent": "Mozilla/5.0 (...) Chrome/124 Safari/537.36"}

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

    for sid, event in SELLERS:
        base_url = f"https://skima.jp/profile/dl_products?id={sid}"
        html = requests.get(base_url, headers=UA).text
        soup = bs4.BeautifulSoup(html, "html.parser")

        ids = {re.search(r'\d+', a['href']).group()
               for a in soup.select('a[href^="/dl/detail"]')
               if re.search(r'\d+', a['href'])}

        prev = set(db.get(sid, []))        # ← 出品者ごとに独立キー
        new  = ids - prev
        print(f"[{sid}] 取得 {len(ids)} 新規 {len(new)}")

        for iid in new:
            title, thumb = scrape_item(iid)
            payload = {
                "username": "SKIMA Watcher",
                "embeds": [{
                    "title": title,
                    "url": f"https://skima.jp/dl/detail?id={iid}",
                    "thumbnail": {"url": thumb},
                    "color": 0xFFCC00,
                    "footer": {"text": f"opt販売 / {sid}"}
                }]
            }
            url = f"https://maker.ifttt.com/trigger/{event}/with/key/{IFTTT_KEY}"
            requests.post(url, json={"value1": json.dumps(payload)}).raise_for_status()

        db[sid] = list(ids)                # 更新（30 日保持したいなら古い方でフィルタ）
