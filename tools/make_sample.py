"""見本データ（架空の価格）を作る。APIのレスポンス形式をまねている。"""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (ASIN, 商品名, 公式定価, [(価格, 出品者, Amazonか, 在庫)], 再販期)
KITS = [
    ("SAMPLE0001", "HG 1/144 ガンダムアストレイ レッドフレーム", 1650,
     [(1350, "Amazon.co.jp", True, True), (2980, "ホビー転売堂", False, True)], "2026年10-12月"),
    ("SAMPLE0002", "HG 1/144 R03 バスターガンダム", 1430,
     [(1200, "Amazon.co.jp", True, True)], "2026年10-12月"),
    ("SAMPLE0003", "HG 1/144 ガンダムアストレイ ブルーフレーム", 1650,
     [(3800, "ホビー転売堂", False, True)], "2026年10-12月"),
    ("SAMPLE0004", "RG 1/144 RX-78-2 ガンダム Ver.2.0", 3300,
     [(2640, "Amazon.co.jp", True, True), (4500, "○○ストア", False, True)], None),
    ("SAMPLE0005", "MG 1/100 ガンダムF91 Ver.2.0", 5500,
     [(5390, "模型のまち（正規取扱店）", False, True)], None),
    ("SAMPLE0006", "HG 1/144 ガンダムエアリアル", 1980,
     [(1584, "Amazon.co.jp", True, True)], None),
    ("SAMPLE0007", "PG UNLEASHED 1/60 RX-78-2 ガンダム", 29700,
     [(24750, "Amazon.co.jp", True, True)], None),
    ("SAMPLE0008", "ENTRY GRADE 1/144 RX-78-2 ガンダム", 990,
     [(990, "Amazon.co.jp", True, True)], None),
    ("SAMPLE0009", "MG 1/100 ガンダムバルバトス", 4950,
     [(9800, "ホビー転売堂", False, True)], None),
    ("SAMPLE0010", "HGUC 1/144 ゼータガンダム", 2420,
     [(1871, "Amazon.co.jp", True, True)], None),
    ("SAMPLE0011", "SDガンダム クロスシルエット フリーダムガンダム", 1320,
     [(1100, "Amazon.co.jp", True, True)], None),
    ("SAMPLE0012", "HG 1/144 R05 イージスガンダム", 1650,
     [(1720, "模型のまち（正規取扱店）", False, True)], "2026年10-12月"),
]

GRADE_COLORS = {"HG": "#1f4fa3", "RG": "#d6372b", "MG": "#13866f", "PG": "#6a3fb5",
                "EN": "#f3b61f", "SD": "#e06b2f", "HGUC": "#1f4fa3"}


def placeholder(title: str) -> str:
    g = title.split()[0][:4]
    color = next((c for k, c in GRADE_COLORS.items() if g.startswith(k)), "#5d6778")
    label = {"ENTR": "EG", "SDガン": "SD"}.get(g, g)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
<rect width="300" height="300" fill="#f3f5f9"/>
<rect x="60" y="70" width="180" height="160" rx="14" fill="{color}" opacity=".9"/>
<rect x="60" y="70" width="180" height="40" rx="14" fill="#fff" opacity=".18"/>
<text x="150" y="170" font-family="sans-serif" font-size="46" font-weight="800" fill="#fff" text-anchor="middle">{label}</text>
<text x="150" y="262" font-family="sans-serif" font-size="14" fill="#8b94a3" text-anchor="middle">見本画像</text></svg>'''
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


items, catalog = [], []
for asin, title, lp, offers, rq in KITS:
    items.append({
        "asin": asin,
        "detailPageURL": "#",
        "itemInfo": {"title": {"displayValue": title}},
        "images": {"primary": {"medium": {"url": placeholder(title)}}},
        "offersV2": {"listings": [{
            "condition": {"value": "New"},
            "availability": {"type": "IN_STOCK" if stock else "OUT_OF_STOCK"},
            "merchantInfo": {"id": "AN1VRQENFRJN5" if amz else "SELLER", "name": name},
            "price": {"money": {"amount": price, "currency": "JPY"}},
            "loyaltyPoints": {"points": round(price * 0.01) if amz else 0},
        } for price, name, amz, stock in offers]},
    })
    catalog.append({"asin": asin, "official_name": title, "official_price": lp,
                    **({"resale_quarter": rq} if rq else {})})

(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "sample_items.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "data" / "catalog.sample.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(items), "items")
