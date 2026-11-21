"""APIの item を整形し、「定価に近く買えるか」を判定する。

方針（規約対応）:
- 価格の履歴は持たない。毎回APIから取り直した「今の値段」だけで判定する。
- 定価は、自前の公式定価（バンダイ公表値）を優先し、なければAPIの参考価格(LIST_PRICE)を使う。
"""
from __future__ import annotations

from dataclasses import dataclass, field

AMAZON_JP_MERCHANT_IDS = {"AN1VRQENFRJN5"}
DEFAULT_TOLERANCE = 0.05  # 定価+5%までは「定価に近い」とみなす


@dataclass
class Offer:
    price: int
    merchant: str
    is_amazon: bool
    in_stock: bool
    points: int = 0


@dataclass
class Product:
    asin: str
    title: str
    url: str
    image: str | None
    list_price: int | None          # 判定に使った定価
    list_price_source: str | None   # "official" | "amazon"
    offers: list[Offer] = field(default_factory=list)
    best: Offer | None = None       # 表示する出品
    resale_quarter: str | None = None

    is_new: bool = False            # 今日からAmazon本体の販売が始まった

    @property
    def market_low(self) -> int | None:
        """表示中の出品より高い、マーケットプレイス出品の値段（概算の比較用）。
        複数あれば中央値を使う。"""
        if not self.best:
            return None
        ps = sorted(o.price for o in self.offers
                    if o.in_stock and not o.is_amazon and o.price > self.best.price)
        if not ps:
            return None
        return ps[len(ps) // 2]

    @property
    def market_off_pct(self) -> int | None:
        m = self.market_low
        if m and self.best:
            return round((1 - self.best.price / m) * 100)
        return None

    @property
    def off_pct(self) -> int | None:
        if self.best and self.list_price:
            return round((1 - self.best.price / self.list_price) * 100)
        return None


def _money(obj: dict | None) -> int | None:
    if not obj:
        return None
    m = obj.get("money", obj)
    amt = m.get("amount")
    return int(round(float(amt))) if amt is not None else None


def normalize(item: dict, catalog: dict) -> Product:
    asin = item.get("asin") or item.get("ASIN")
    info = item.get("itemInfo", {})
    title = (info.get("title") or {}).get("displayValue", asin)
    img = (((item.get("images") or {}).get("primary") or {}).get("medium") or {}).get("url")
    url = item.get("detailPageURL") or f"https://www.amazon.co.jp/dp/{asin}"

    offers: list[Offer] = []
    amazon_list_price: int | None = None
    for lst in ((item.get("offersV2") or {}).get("listings") or []):
        cond = ((lst.get("condition") or {}).get("value") or "New")
        if cond.lower() != "new":
            continue
        price = _money(lst.get("price"))
        if price is None:
            continue
        basis = (lst.get("price") or {}).get("savingBasis")
        if basis and basis.get("savingBasisType") == "LIST_PRICE":
            amazon_list_price = amazon_list_price or _money(basis)
        merch = lst.get("merchantInfo") or {}
        name = merch.get("name", "")
        is_amz = merch.get("id") in AMAZON_JP_MERCHANT_IDS or name.startswith("Amazon")
        avail = ((lst.get("availability") or {}).get("type") or "IN_STOCK").upper()
        points = int(((lst.get("loyaltyPoints") or {}).get("points")) or 0)
        offers.append(Offer(price, name, is_amz, avail == "IN_STOCK", points))

    cat = catalog.get(asin, {})
    if cat.get("official_price"):
        lp, src = int(cat["official_price"]), "official"
    elif amazon_list_price:
        lp, src = amazon_list_price, "amazon"
    else:
        lp, src = None, None

    return Product(asin, title, url, img, lp, src, offers,
                   resale_quarter=cat.get("resale_quarter"))


def choose_fair_offer(p: Product, tolerance: float = DEFAULT_TOLERANCE) -> Offer | None:
    """「定価に近く・正規に買える」出品を1つ選ぶ。なければ None。"""
    stock = [o for o in p.offers if o.in_stock]
    if not stock:
        return None
    amazon = [o for o in stock if o.is_amazon]
    if p.list_price:
        limit = p.list_price * (1 + tolerance)
        fair = [o for o in stock if o.price <= limit]
        # Amazon本体の出品を優先、その中で最安
        fair.sort(key=lambda o: (not o.is_amazon, o.price))
        return fair[0] if fair else None
    # 定価が不明なら Amazon本体の出品だけを採用（転売価格の混入を避ける）
    return min(amazon, key=lambda o: o.price) if amazon else None


def pick_fair(products: list[Product], tolerance: float = DEFAULT_TOLERANCE) -> list[Product]:
    out = []
    for p in products:
        p.best = choose_fair_offer(p, tolerance)
        if p.best:
            out.append(p)
    out.sort(key=lambda p: (-max(p.off_pct or 0, p.market_off_pct or 0), p.best.price))
    return out
