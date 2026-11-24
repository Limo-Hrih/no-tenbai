"""collect_amazon.js の結果（1行1商品）から、実データの試作ページを作る。

  python tools/make_real.py today.txt [--prev yesterday.txt] [--out preview.html]

- 画像はAmazonの画像サーバーから取得し、余白を切って天地をそろえてページに埋め込む
- --prev を渡すと、前日にAmazon本体の販売がなかった商品に「NEW」を付け、
  「今日Amazon本体で買えるようになったガンプラ」枠に出す
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
S, PAD = 220, 6


# ガンプラではない商品（食玩など）。収集側でも弾いているが、念のためここでも除く
NOT_KIT = re.compile(r"食玩|チューインガム|ガム|CONVERGE|ウエハー|BOX販売", re.I)


def parse(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        a, amz, lp, med, n, img, title = line.split("|", 6)
        if NOT_KIT.search(title):
            continue
        rows.append(dict(asin=a.replace(".", ""), amazon=int(amz) if amz else None,
                         lp=int(lp) if lp else None, med=int(med) if med else None,
                         n=int(n or 0), img=img.replace(".", ""), title=title))
    return rows


def image_uri(img_id: str) -> str | None:
    if not img_id:
        return None
    try:
        data = urllib.request.urlopen(
            f"https://m.media-amazon.com/images/I/{img_id}._AC_SX220_.jpg", timeout=20).read()
        im = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        return None
    mask = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))) \
        .convert("L").point(lambda v: 255 if v > 18 else 0)
    if mask.getbbox():
        im = im.crop(mask.getbbox())
    w, h = im.size
    sc = min((S - 2 * PAD) / h, (S - 2 * PAD) / w)
    im = im.resize((max(1, round(w * sc)), max(1, round(h * sc))), Image.LANCZOS)
    can = Image.new("RGB", (S, S), (255, 255, 255))
    can.paste(im, ((S - im.size[0]) // 2, (S - im.size[1]) // 2))
    buf = io.BytesIO()
    can.save(buf, "JPEG", quality=74)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("today")
    ap.add_argument("--prev")
    ap.add_argument("--prev-asins", help="前日にAmazon本体が販売していたASINのJSON配列ファイル")
    ap.add_argument("--save-asins", help="今日Amazon本体が販売しているASINをこのJSONに保存")
    ap.add_argument("--lite", action="store_true", help="Amazonの価格・画像を載せないテスト公開版を作る")
    ap.add_argument("--notice", default="")
    ap.add_argument("--out", default=str(Path.home() / "preview_real.html"))
    args = ap.parse_args()

    rows = parse(Path(args.today))
    items, catalog = [], []
    for r in rows:
        listings = []
        if r["amazon"]:
            listings.append({"condition": {"value": "New"}, "availability": {"type": "IN_STOCK"},
                             "merchantInfo": {"id": "AN1VRQENFRJN5", "name": "Amazon.co.jp"},
                             "price": {"money": {"amount": r["amazon"]}}})
        if r["med"]:
            # 中央値だけを保持しているので、マケプレ出品として1件で表す
            listings.append({"condition": {"value": "New"}, "availability": {"type": "IN_STOCK"},
                             "merchantInfo": {"id": "MKT", "name": "マーケットプレイス"},
                             "price": {"money": {"amount": r["med"]}}})
        items.append({"asin": r["asin"], "detailPageURL": f"https://www.amazon.co.jp/dp/{r['asin']}?tag=limolimo-22",
                      "itemInfo": {"title": {"displayValue": r["title"]}},
                      "images": {"primary": {"medium": {"url": image_uri(r["img"])}}},
                      "offersV2": {"listings": listings}})
        c = {"asin": r["asin"], "official_name": r["title"]}
        if r["lp"]:
            c["official_price"] = r["lp"]
        catalog.append(c)

    data = ROOT / "data"
    # 公式の再販リスト（改定後の定価）と結び付ける
    official = {}
    for grp in json.loads((data / "resale.json").read_text(encoding="utf-8")):
        for it in grp["items"]:
            if it.get("asin"):
                official[it["asin"]] = (it["price_after"], grp["quarter"])
    for c in catalog:
        if c["asin"] in official:
            c["official_price"], c["resale_quarter"] = official[c["asin"]]
    (data / "real_items.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    (data / "catalog.real.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    # 前日にAmazon本体の販売があったASIN（--prev）を「前回の状態」として渡す
    state = data / "sample_prev_amazon_asins.json.real"
    prev = None
    if args.prev:
        prev = [r["asin"] for r in parse(Path(args.prev)) if r["amazon"]]
    elif args.prev_asins and Path(args.prev_asins).exists():
        prev = json.loads(Path(args.prev_asins).read_text())
    # 過去の日別ファイル（今日の分は除く）に一度でも出たASIN＝再入荷判定用
    seen_file = data / "seen_amazon_asins.json.real"
    daily = data / "state" / "daily"
    head = Path(args.today).read_text(encoding="utf-8").split("\n", 1)[0]
    m = re.match(r"#\s*(\d{4}-\d{2}-\d{2})", head)
    today_date = m.group(1) if m else "9999-99-99"
    seen = set()
    for fp in sorted(daily.glob("*.json")):
        if fp.stem >= today_date:  # 今日以降の分は「過去」に含めない
            continue
        seen |= set(json.loads(fp.read_text()))
    seen_file.write_text(json.dumps(sorted(seen)))
    if prev is not None:
        state.write_text(json.dumps(prev))
    elif state.exists():
        state.unlink()

    subprocess.run([sys.executable, str(ROOT / "src" / "build.py"), "--real-snapshot",
                    "--out", args.out] + (["--lite"] if args.lite else [])
                   + (["--notice", args.notice] if args.notice else []), check=True)
    today_amz = [r for r in rows if r["amazon"]]
    print(f"Amazon本体の販売: {len(today_amz)}点")
    if args.save_asins:
        Path(args.save_asins).parent.mkdir(parents=True, exist_ok=True)
        Path(args.save_asins).write_text(json.dumps(sorted(r["asin"] for r in today_amz), indent=0))
    if prev is not None:
        new = [r for r in today_amz if r["asin"] not in set(prev)]
        restock = [r for r in new if r["asin"] in seen]
        print(f"今日から買えるようになった: {len(new)}点（うち再入荷 {len(restock)}点・新登場 {len(new) - len(restock)}点）")
        for r in new:
            print(f"  {'再入荷' if r['asin'] in seen else 'NEW'} {r['asin']} ¥{r['amazon']} {r['title'][:50]}")
    gone = sorted(set(prev or []) - {r["asin"] for r in today_amz})
    if prev is not None:
        titles = {r["asin"]: r["title"] for r in rows}
        print(f"販売が消えた: {len(gone)}点")
        for a in gone:
            print(f"  GONE {a} {titles.get(a, '（今日の一覧になし）')[:50]}")


if __name__ == "__main__":
    main()
