"""モビルスーツアキネーターチャレンジに出す「Amazonで買えるガンプラ」のデータを作る。

使い方: python tools/make_akinator_feed.py /home/claude/today.txt --out /home/claude/gunpla.json

出力（JSON）:
  date   : データを集めた日（today.txt の先頭行）
  top3   : ページ下に出す「売れ筋で、しかも安い」3点
           条件＝Amazon本体の販売・過去1か月の購入数あり・参考価格から20%以上安い
           並び＝購入数の多い順、同じなら割引率の高い順（2026-11-28 マスター決定）
  items  : Amazon本体で今買えるキット全部（結果画面で、その問題の機体のキットを探すのに使う）
各商品: asin, name（短い商品名）, title（元の商品名）, price, list_price, off（割引率%）, bought（過去1か月の購入数）,
        img（Amazonの商品画像URL）, url（アソシエイトタグ付きの商品ページ）
価格・画像・商品名はAmazonのデータなので、このリポジトリ（公開）にはコミットしない。
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
from render import short_title  # noqa: E402
from make_real import parse  # noqa: E402

TAG = "limolimo-22"


def tidy(t: str) -> str:
    s = short_title(t)
    s = re.sub(r"\s+(プラスチック製\s*)?(色分け済み)?プラモデル(\s.*)?$", "", s)
    s = re.sub(r"^ENTRY GRADE\s+EG\b|^ENTRY GRADE\b|^EG ENTRY GRADE\b", "EG", s)
    s = re.sub(r"^(HGUC|HGCE|HGAC|HGFC|HG|MG|RG)\s+\d{2,3}\s+", r"\1 ", s)
    return re.sub(r"\s{2,}", " ", s).strip() or t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("today")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    head = Path(args.today).read_text(encoding="utf-8").split("\n", 1)[0]
    m = re.match(r"#\s*(\d{4}-\d{2}-\d{2})", head)
    items = []
    for r in parse(Path(args.today)):
        if not r["amazon"]:
            continue
        off = round((1 - r["amazon"] / r["lp"]) * 100) if r["lp"] and r["lp"] > r["amazon"] else 0
        items.append({
            "asin": r["asin"], "name": tidy(r["title"]), "title": r["title"],
            "price": r["amazon"], "list_price": r["lp"], "off": off, "bought": r["bought"] or 0,
            "img": f"https://m.media-amazon.com/images/I/{r['img']}._AC_SL300_.jpg" if r["img"] else None,
            "url": f"https://www.amazon.co.jp/dp/{r['asin']}?tag={TAG}",
        })
    top3 = sorted([x for x in items if x["bought"] and x["off"] >= 20],
                  key=lambda x: (-x["bought"], -x["off"]))[:3]
    out = {"date": m.group(1) if m else None, "top3": top3, "items": items}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"items {len(items)}点 / top3:")
    for x in top3:
        print(f"  {x['name']} ¥{x['price']:,}（{x['off']}%オフ・1か月で{x['bought']}点以上購入）")


if __name__ == "__main__":
    main()
