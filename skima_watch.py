import re, os, requests, bs4, shelve, pathlib
from datetime import datetime, timedelta

SELLER_ID = "151777"                      # ←監視したい出品者のID
BASE_URL  = f"https://skima.jp/profile/dl_products?id={SELLER_ID}"
IFTTT_KEY = os.getenv("IFTTT_KEY")        # GitHub Secrets から取得
IFTTT_URL = f"https://maker.ifttt.com/trigger/skima_opt_new/with/key/{IFTTT_KEY}"
KEEP_DAYS = 30

# .github/actions/cache に保存すると GitHub Actions 側で永続化しやすい
CACHE     = pathlib.Path(".cache")
CACHE.mkdir(exist_ok=True)
DB_PATH   = str(CACHE / "items.db")
print("TEST1")
with shelve.open(DB_PATH) as db:
    prev = db.get("items", {})

    html = requests.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"}).text

    soup  = bs4.BeautifulSoup(html, "html.parser")
    selector = 'a[href^="/dl/detail"]'           # 汎用化
    items = set()
    
    print("TEST2")
    for a in soup.select(selector):
        print("TEST2-1")
        m = re.search(r'\d+', a['href'])
        if m:
            items.add(m.group())
            print("TEST2-2")
    
    print("取得:", len(items), "件", list(items)[:5])
    
    new = [iid for iid in items if iid not in prev]
    print("新規:", new)
    
    for iid in new:
        print("TEST3")
        data = {"value1": f"https://skima.jp/dl/detail?id={iid}"}
        r = requests.post(IFTTT_URL, json=data)
        print("POST", iid, "→", r.status_code)
        r.raise_for_status()

    # --- 古い ID を整理 ---
    now = datetime.utcnow().isoformat()
    for iid in items:
        prev.setdefault(iid, now)

    cutoff = datetime.utcnow() - timedelta(days=KEEP_DAYS)
    prev = {iid: ts for iid, ts in prev.items()
            if datetime.fromisoformat(ts) > cutoff}

    db["items"] = prev
