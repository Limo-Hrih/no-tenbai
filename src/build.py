"""サイトを生成する。

  python src/build.py            # 本番：Creators APIから今の価格を取得
  python src/build.py --sample   # 見本データで生成（APIを呼ばない）

Amazonから取得した価格・画像URLはファイルに保存せず、HTMLの生成にだけ使う
（規約上、画像以外も24時間までしか保存できないため。HTMLは毎日作り直す）。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from render import render  # noqa: E402
from select_items import normalize, pick_fair  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
JST = timezone(timedelta(hours=9))


def load(name: str):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "dist" / "index.html"))
    ap.add_argument("--tolerance", type=float, default=0.05)
    args = ap.parse_args()

    catalog_file = "catalog.sample.json" if args.sample else "catalog.json"
    catalog = {c["asin"]: c for c in load(catalog_file)}
    resale = load("resale.json")

    if args.sample:
        raw_items = load("sample_items.json")
    else:
        from creators_api import CreatorsClient
        client = CreatorsClient()
        raw_items = client.get_items(list(catalog))

    products = [normalize(it, catalog) for it in raw_items]
    fair = pick_fair(products, args.tolerance)

    # 「今日Amazon本体で買えるようになった」判定。保存するのはASINの一覧だけ
    # （ASINは無期限に保存してよいと規約に明記されている）。
    state_file = ROOT / "data" / ("sample_prev_amazon_asins.json" if args.sample
                                  else "state/amazon_asins.json")
    prev = set(json.loads(state_file.read_text())) if state_file.exists() else None
    current = sorted(p.asin for p in fair if p.best.is_amazon)
    if prev is not None:
        for p in fair:
            p.is_new = p.best.is_amazon and p.asin not in prev
    if not args.sample:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(current, indent=0))

    # 再販リストの各商品に、カタログ上のASINを結び付ける
    by_name = {c.get("official_name"): a for a, c in catalog.items() if c.get("official_name")}
    for grp in resale:
        for r in grp["items"]:
            r.setdefault("asin", by_name.get(r["name"]))

    html = render(fair, resale, datetime.now(JST), sample=args.sample)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"{len(raw_items)}件を確認 → 定価で買える {len(fair)}件 → {out}")


if __name__ == "__main__":
    main()
