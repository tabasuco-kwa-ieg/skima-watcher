import os, requests, bs4, shelve, pathlib

SELLER_ID = "151777"                      # ←監視したい出品者のID
BASE_URL  = f"https://skima.jp/profile/dl_products?id={SELLER_ID}"
IFTTT_KEY = os.getenv("IFTTT_KEY")        # GitHub Secrets から取得
IFTTT_URL = f"https://maker.ifttt.com/trigger/skima_opt_new/with/key/{IFTTT_KEY}"

# .github/actions/cache に保存すると GitHub Actions 側で永続化しやすい
CACHE     = pathlib.Path(".cache")
CACHE.mkdir(exist_ok=True)
DB_PATH   = str(CACHE / "items.db")
print("TEST1")
with shelve.open(DB_PATH) as db:
    print("TEST2")
    prev = set(db.get("items", []))

    html  = requests.get(BASE_URL, headers={"User-Agent":"Mozilla/5.0"}).text
    soup  = bs4.BeautifulSoup(html, "html.parser")
    items = {a["href"].split("=")[1]
             for a in soup.select('a[href*=\"/item/detail?item_id=\"]')}

    for iid in items - prev:
        url = f"https://skima.jp/item/detail?item_id={iid}"
        resp = requests.post(IFTTT_URL, json={"value1": url})
        print("POST",url)
        print("→",resp.status_code, resp.text[:120])
        resp.raise_for_status()

    if items != prev:
        db["items"] = list(items)

    if not items - prev:
        print("（テスト送信）差分が無いのでダミーを送ります")
        requests.post(IFTTT_URL, json={"content": "Ping from CI"})

