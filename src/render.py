"""静的HTMLを1枚生成する。"""
from __future__ import annotations

import html
import re
from datetime import datetime

from select_items import Product
import base64 as _b64
from pathlib import Path as _Path
_LOGO = _Path(__file__).resolve().parent.parent / "assets" / "logo.png"
LOGO_URI = ("data:image/png;base64," + _b64.b64encode(_LOGO.read_bytes()).decode()) if _LOGO.exists() else ""

SITE_NAME = "NO転売！ガンプラカタログ"
SITE_TAGLINE = "転売価格はNo！ 正規の値段で買えるガンプラ情報だけを毎日まとめています。"
SITE_TAGLINE_HTML = "転売価格はNo！ 正規の値段で買えるガンプラ情報だけを毎日まとめています。"

GRADES = ["HG", "RG", "MG", "PG", "EG", "SD"]


def grade_of(title: str) -> str:
    t = title.upper()
    for g, pat in [("PG", r"\bPG\b|PERFECT GRADE"), ("MG", r"\bMG\b|MASTER GRADE"),
                   ("RG", r"\bRG\b|REAL GRADE"), ("EG", r"\bEG\b|ENTRY GRADE"),
                   ("HG", r"\bHG|HIGH GRADE"), ("SD", r"\bSD\b|BB戦士|SDCS|SDEX")]:
        if re.search(pat, t):
            return g
    return "SD"  # SD・ガンプラくん・ベストメカなどはまとめて「SD」ボタンで表示


SERIES = ["機動戦士ガンダム 水星の魔女", "機動戦士ガンダム 鉄血のオルフェンズ", "機動戦士ガンダム 閃光のハサウェイ キルケーの魔女",
          "機動戦士ガンダム 閃光のハサウェイ", "機動戦士ガンダム 逆襲のシャア", "機動戦士ガンダム 第08MS小隊", "機動戦士ガンダム THE ORIGIN",
          "機動戦士Gundam GQuuuuuuX", "機動戦士ガンダムSEED FREEDOM", "機動戦士ガンダムSEED DESTINY", "機動戦士ガンダムSEED ASTRAY",
          "機動戦士ガンダムSEED ECLIPSE", "機動戦士ガンダムSEED", "機動戦士ガンダムAGE", "機動戦士ガンダムUC", "機動戦士ガンダムZZ",
          "機動戦士ガンダム00", "機動戦士Zガンダム", "機動戦士Vガンダム", "機動戦士ガンダムF91", "機動戦士ガンダムRG",
          "新機動戦記ガンダムW Endless Waltz", "新機動戦記ガンダムW", "機動武闘伝Gガンダム", "ガンダムGのレコンギスタ",
          "機動戦士ガンダム", "-GUNPLA EVOLUTION PROJECT-", "SDガンダム"]


def short_title(t: str) -> str:
    s = re.sub(r"\s*[（(][^）)]*(機動|ガンダム|Gundam|ASTRAY)[^）)]*[）)]", "", t)
    for ser in SERIES:
        s = s.replace(ser + " ", "").replace(ser, "")
    s = re.sub(r"1/\d+(スケール)?", "", s)
    s = re.sub(r"\s+\d{5,}$|\s+BAS\d+", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s or t


UC_KEYS = ["HGUC", "宇宙世紀", "機動戦士Zガンダム", "ガンダムZZ", "逆襲のシャア", "ガンダムUC", "ユニコーン", "F91", "Vガンダム",
           "閃光のハサウェイ", "0080", "0083", "第08MS小隊", "THE ORIGIN", "GQuuuuuuX", "ガンダムNT", "クロスボーン",
           "RX-78", "ザク", "ジオン", "ガンキャノン", "ガンタンク", "サザビー", "νガンダム", "Hi-ν", "シナンジュ", "クシャトリヤ",
           "ゼータ", "Mk-II", "ジオング", "グフ", "ドム", "ギャン", "ゲルググ", "メッサー", "Ξガンダム", "アリュゼウス", "バウ", "ガンダムZERO"]
ANOTHER_KEYS = ["SEED", "ストライク", "フリーダム", "ジャスティス", "アストレイ", "ガンダム00", "ダブルオー", "エクシア",
                "ガンダムW", "ウイング", "ヘビーアームズ", "デスサイズ", "シェンロン", "エピオン", "Gガンダム", "ゴッドガンダム",
                "シャイニング", "HGFC", "HGAC", "HGCE", "ガンダムAGE", "レギルス", "鉄血", "バルバトス", "バエル", "グレイズ",
                "キマリス", "水星の魔女", "エアリアル", "ルブリス", "ディランザ", "ベギル", "デミトレーナー", "ガンダムX",
                "∀ガンダム", "ターンエー", "レコンギスタ", "G-セルフ", "エクリプス"]


def era_of(title: str) -> str:
    t = title
    if grade_of(t) == "SD" or any(k in t for k in ("三国創傑伝", "SDW HEROES", "ガンプラくん", "EXスタンダード", "BB戦士")):
        return "SD・その他"
    if any(k in t for k in ANOTHER_KEYS):
        return "アナザー"
    if any(k in t for k in UC_KEYS):
        return "宇宙世紀"
    return "SD・その他"


def yen(n: int | None) -> str:
    return "—" if n is None else f"¥{n:,}"


def e(s) -> str:
    return html.escape(str(s), quote=True)


def card(p: Product, stamp: str) -> str:
    b = p.best
    off = p.off_pct
    moff = p.market_off_pct
    if moff is not None and moff >= 10 and moff >= (off or 0):
        badge = f'<div class="badge"><span class="badge-l">転売相場より</span><span class="badge-n">−{moff}%</span></div>'
    elif off is not None and off > 0:
        badge = f'<div class="badge"><span class="badge-l">定価より</span><span class="badge-n">−{off}%</span></div>'
    elif p.list_price:
        badge = '<div class="badge badge-even"><span class="badge-n">定価</span></div>'
    else:
        badge = '<div class="badge badge-even"><span class="badge-n">正規販売</span></div>'
    img = f'<img src="{e(p.image)}" alt="" loading="lazy">' if p.image else '<div class="noimg">NO IMAGE</div>'
    tags = ""
    best_off = max(off or 0, moff or 0)
    if best_off >= 50:
        tags += '<span class="tg tg-half">半額以下！</span>'
    elif best_off >= 30:
        tags += '<span class="tg tg-big">大幅値下げ中</span>'
    if p.is_new:
        tags += '<span class="tg tg-new">NEW</span>'
    if p.resale_quarter:
        tags += '<span class="tg tg-re">再販</span>'
    meta = []
    if p.list_price and p.list_price > b.price:
        meta.append(f"希望価格 <s>{yen(p.list_price)}</s>")
    if moff is not None and moff >= 10:
        meta.append(f"転売相場 <s>{yen(p.market_low)}</s>")
    meta_html = "".join(f'<div class="meta">{m}</div>' for m in meta)
    return f'''
<a class="card" href="{e(p.url)}" target="_blank" rel="sponsored noopener" data-grade="{e(grade_of(p.title))}" data-era="{e(era_of(p.title))}" data-off="{max(off or 0, moff or 0)}" data-price="{b.price}">
  <div class="thumb">{img}{badge}{f'<div class="tags">{tags}</div>' if tags else ''}</div>
  <div class="body">
    <h3 title="{e(p.title)}">{e(short_title(p.title))}</h3>
    <div class="price"><span class="yen">¥</span>{b.price:,}</div>
    {meta_html}
  </div>
</a>'''


def resale_rows(resale: list[dict], fair_by_asin: dict[str, Product], stamp: str) -> str:
    rows = []
    for r in resale:
        p = fair_by_asin.get(r.get("asin") or "")
        if p and p.best:
            status = (f'<a class="status ok" href="{e(p.url)}" target="_blank" rel="sponsored noopener">'
                      f'{buy_label(p)}<small>（{e(stamp)}時点）</small></a>')
        else:
            status = '<span class="status wait">Amazon本体の販売は確認できず</span>'
        before = r.get("price_before")
        rows.append(f'''
<tr data-grade="{e(grade_of(r["name"]))}">
  <td class="rn">{e(r["name"])}</td>
  <td class="rp">{yen(r.get("price_after"))}{f'<small>旧 {yen(before)}</small>' if before else ''}</td>
  <td class="rs">{status}</td>
</tr>''')
    return "\n".join(rows)


def buy_label(p: Product) -> str:
    if p.list_price and p.best.price > p.list_price:
        return f"Amazonで定価に近い値段 {yen(p.best.price)}"
    return f"Amazonで定価以下 {yen(p.best.price)}"


def _norm(s: str) -> str:
    s = re.sub(r"1/\d+", "", s)
    return re.sub(r"[\s・()（）\[\]]", "", s).upper()


_GRADES = ("HGUC", "HGCE", "HGFC", "HGAC", "HGAW", "MGSD", "HG", "RG", "MG", "PG", "RE/100", "EG")


def _clean(s: str, keep_space: bool = False) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKC", s).upper()
    s = s.replace("Ⅱ", "II").replace("Ⅲ", "III").replace("ダブルゼータ", "ZZ")
    s = re.sub(r"1/\d+", " ", s)
    s = re.sub(r"[・()（）\[\]［］\-‐=+＋.,{}]", " " if keep_space else "", s)
    return re.sub(r"\s+", "|" if keep_space else "", s).strip("|")


_KANA = "ァ-ヴー"


def pred_match(name: str, title: str) -> bool:
    """再販情報の商品名（「HGUC ガンダムEz-8」など）がAmazonの商品名に当たるか。
    グレードが一致し、名前の各語がAmazon側の語の切れ目にそろって含まれていれば一致とみなす
    （「ジ・オ」が「ジオング」に、「ヴィダール」が「キマリスヴィダール」に当たらないように）。"""
    name = re.sub(r"（[^）]*(店|空港|サイドF|サテライト|東京|福岡|渋谷|新千歳|同)[^）]*）", "", name).strip()
    words = name.split()
    if not words:
        return False
    g = words[0].upper()
    if g in _GRADES:
        words = words[1:]
        tg = title.upper()
        if g == "HG":
            ok = re.search(r"(?<![A-Z])HG(UC|CE|FC|AC|AW)?(?![A-Z])", tg)
        else:
            ok = re.search(r"(?<![A-Z])" + re.escape(g) + r"(?![A-Z])", tg)
        if not ok:
            return False
    t = "|" + _clean(title, keep_space=True) + "|"
    keys = [k for k in (_clean(w) for w in words) if k and k != "ガンダム"]
    if not keys:
        return False
    for k in keys:
        pat = r"\|?".join(re.escape(c) for c in k)
        if not re.search(f"(?<![{_KANA}]){pat}(?![{_KANA}])", t):
            return False
    return True


def predictions_html(pred: dict | None, fair: list[Product]) -> str:
    if not pred:
        return ""
    fair_by_title = {p.title: p for p in fair}
    days = []
    for d in pred["days"]:
        lis = []
        for name in d["items"]:
            hit = next((p for t, p in fair_by_title.items() if pred_match(name, t)), None)
            tail = (f' <a class="status ok" href="{e(hit.url)}" target="_blank" rel="sponsored noopener">'
                    f'{buy_label(hit)}</a>') if hit else ""
            lis.append(f"<li>{e(name)}{tail}</li>")
        cls = "pk-pred" if d["kind"] == "予測" else "pk-real"
        days.append(f'''<div class="pday"><div class="pdate">{e(d["date"])}
  <span class="pk {cls}">{e(d["kind"])}</span></div><ul>{"".join(lis)}</ul></div>''')
    hits = sum(1 for d in pred["days"] for n in d["items"]
               if any(pred_match(n, t) for t in fair_by_title))
    extra = ""
    if pred.get("december"):
        lis = []
        for name in pred["december"]:
            hit = next((p for t, p in fair_by_title.items() if pred_match(name, t)), None)
            tail = (f' <a class="status ok" href="{e(hit.url)}" target="_blank" rel="sponsored noopener">'
                    f'{buy_label(hit)}</a>') if hit else ""
            lis.append(f"<li>{e(name)}{tail}</li>")
        extra += f'''<div class="pday pwide"><div class="pdate">12月の再販予定（日付未定）
  <span class="pk pk-pred">予測</span></div><ul class="cols">{"".join(lis)}</ul></div>'''
    for g in pred.get("pbandai", []):
        extra += f'''<div class="pday"><div class="pdate">プレバン再販 {e(g["date"])}
  <span class="pk pk-pb">受付</span></div><ul>{"".join(f"<li>{e(n)}</li>" for n in g["items"])}</ul></div>'''
    srcs = "・".join(f'<a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["name"])}</a>'
                    for s in pred["sources"])
    return f'''
<section class="rq pred">
  <h3>再販予想・入荷報告 <small>{e(pred["week"])}（{e(pred.get("updated", ""))}更新）</small></h3>
  <p class="src">{e(pred["note"])}<br>出典：{srcs}</p>
  <p class="src">このうち <b>{hits}件</b> は、いまAmazonで定価以下・定価並みで買えます（緑のボタン）。</p>
  <div class="pgrid">{"".join(days)}{extra}</div>
</section>'''


def render(fair: list[Product], resale_groups: list[dict], generated_at: datetime,
           sample: bool = False, pred: dict | None = None, snapshot: bool = False) -> str:
    stamp = generated_at.strftime("%Y/%m/%d %H:%M")
    fair_by_asin = {p.asin: p for p in fair}
    pred_names = [n for d in (pred or {}).get("days", []) for n in d["items"]] + list((pred or {}).get("december", []))
    def in_pred(p):
        return any(pred_match(n, p.title) for n in pred_names)
    featured = [p for p in fair if p.is_new or p.resale_quarter or in_pred(p)]
    featured.sort(key=lambda p: (not p.is_new, -max(p.off_pct or 0, p.market_off_pct or 0)))
    for p in featured:
        if in_pred(p) and not p.resale_quarter:
            p.resale_quarter = "再販"
    fset = {p.asin for p in featured}
    rest = [p for p in fair if p.asin not in fset]
    featured_html = "\n".join(card(p, stamp) for p in featured) or '<p class="empty">いまAmazonで定価以下になっている再販品はありません。</p>'
    cards = "\n".join(card(p, stamp) for p in rest) or '<p class="empty">いま該当する商品はありません。</p>'
    new_items = [p for p in fair if p.is_new]
    new_html = (f'''
<section class="newbox">
  <h2>今日Amazon本体で買えるようになったガンプラ <small>{len(new_items)}点</small></h2>
  <div class="grid">{"".join(card(p, stamp) for p in new_items)}</div>
</section>''' if new_items else "")
    grade_btns = "".join(
        f'<button class="f" data-g="{g}">{g}</button>' for g in GRADES)

    resale_html = []
    for grp in resale_groups:
        resale_html.append(f'''
<section class="rq">
  <h3>{e(grp["quarter"])} 一般販売の再販商品 <small>（{len(grp["items"])}点）</small></h3>
  <p class="src">出典：<a href="{e(grp["source"])}" target="_blank" rel="noopener">バンダイ ホビーサイト「再販商品の価格改定のお知らせ」</a>（{e(grp.get("updated", ""))}更新）。価格は改定後のメーカー希望小売価格です。店舗によって入荷する商品は異なります。</p>
  <table class="rt"><thead><tr><th>商品名</th><th>定価</th><th>Amazonの状況</th></tr></thead>
  <tbody>{resale_rows(grp["items"], fair_by_asin, stamp)}</tbody></table>
</section>''')

    if snapshot:
        sample_banner = (f'<div class="sample">試作版：{e(stamp)}ごろにAmazon.co.jpの検索結果から集めた実データです（非公開の確認用）。'
                         '本番ではAmazonのAPIで毎日自動更新します。「今日から」の枠は2日分のデータがそろうと表示されます。</div>')
    else:
      sample_banner = ('<div class="sample">これは見本データによる試作画面です。表示中の価格・商品はすべて架空です。</div>'
                     if sample else "")

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{SITE_NAME}｜転売価格なしで買えるガンプラ</title>
<meta name="description" content="{SITE_TAGLINE}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;800&family=Orbitron:wght@700;900&family=Oxanium:wght@700;800&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:#f4f8f7; --panel:#ffffff; --panel2:#ffffff; --line:#d9e7e3; --line2:#9fd8c4;
  --ink:#1d2b2a; --sub:#6b7f7a; --mint:#10a37a; --mint-soft:#0b8a66; --amber:#e8281e; --sale:#d81f17; --alert:#ef4f43; --sky:#2b8fd6;
  --mono:"Oxanium","Share Tech Mono",ui-monospace,monospace; --digi:"Orbitron","Oxanium",sans-serif;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"M PLUS Rounded 1c","Hiragino Sans","Noto Sans JP",sans-serif; color:var(--ink); line-height:1.6;
  background:
    radial-gradient(1200px 600px at 15% -10%, rgba(16,163,122,.08), transparent 60%),
    radial-gradient(900px 500px at 100% 0%, rgba(43,143,214,.06), transparent 60%),
    repeating-linear-gradient(0deg, rgba(16,163,122,.06) 0 1px, transparent 1px 28px),
    repeating-linear-gradient(90deg, rgba(16,163,122,.06) 0 1px, transparent 1px 28px),
    var(--bg); }}
a {{ color:inherit; }}
.pr {{ background:#fff; border-bottom:1px solid var(--line); font-size:11px; color:var(--sub); text-align:center; padding:3px 8px; }}
header {{ background:#fff; border-bottom:2px solid var(--mint); padding:10px 20px 8px;
  box-shadow:0 6px 20px rgba(16,163,122,.10); }}
.hwrap, main, footer .fwrap {{ max-width:1180px; margin:0 auto; }}

.logo .mark {{ width:30px; height:30px; border:2px solid var(--mint); border-radius:8px; position:relative; box-shadow:0 0 10px rgba(16,163,122,.35); }}
.logo .mark::after {{ content:""; position:absolute; inset:7px; border-radius:3px; background:var(--mint); opacity:.85; }}
.logo .no {{ color:var(--alert); }}
.live {{ font-family:var(--mono); font-size:11px; color:var(--mint); border:1px solid var(--line2); border-radius:999px; padding:1px 8px; margin-left:4px; letter-spacing:.08em; }}
.live::before {{ content:"●"; margin-right:5px; animation:blink 1.6s infinite; }}
@keyframes blink {{ 50% {{ opacity:.25; }} }}

.brand {{ display:flex; align-items:center; gap:16px; min-height:64px; }}
.stripes {{ display:flex; gap:4px; }} .stripes i {{ width:11px; height:20px; background:var(--mint); transform:skewX(-28deg); display:block; }}
.stripes i:nth-child(2) {{ opacity:.8; }} .stripes i:nth-child(3) {{ opacity:.6; }}
.anti {{ font: inherit; letter-spacing:inherit; color:inherit; }}
.anti .u {{ display:block; height:2px; margin-top:7px; background:#c9d6d2; width:150px; position:relative; }}
.anti .u b {{ position:absolute; left:0; top:0; height:2px; width:40px; background:var(--mint); }}
.vsep {{ width:1px; align-self:stretch; background:#cfdcd8; margin:6px 0; }}
.logo {{ margin:0; line-height:0; }} .logo img {{ height:70px; width:auto; display:block; }}
.sys {{ font-family:var(--mono); font-size:14px; font-weight:800; letter-spacing:.16em; color:#0d2147; line-height:1.55; display:flex; align-items:center; gap:10px; white-space:nowrap; }}
.online {{ font-family:var(--mono); font-size:14px; font-weight:800; letter-spacing:.12em; color:#0d1f3c; display:flex; align-items:center; gap:7px; margin-left:auto; white-space:nowrap; }}
.online .sq {{ width:11px; height:11px; background:var(--mint); animation:blink 1.6s infinite; }}
.online small {{ font-family:inherit; font-size:11px; color:var(--sub); letter-spacing:.04em; font-weight:700; }}
@media (max-width:1000px) {{ .hide-md {{ display:none !important; }} }}
@media (max-width:640px) {{ .hide-sm {{ display:none !important; }} .logo img {{ height:44px; }} .brand {{ gap:10px; min-height:48px; }}
  .online small {{ display:none; }} .online {{ font-size:11px; }} .stripes i {{ width:8px; height:15px; }} }}
.tag {{ margin:4px 0 0; color:var(--sub); font-size:13px; }}
.tabs {{ display:flex; gap:6px; margin-top:12px; }}
.tab {{ border:1px solid transparent; border-bottom:none; background:transparent; color:var(--sub); font:inherit; font-weight:700; font-size:14px;
  padding:8px 16px; border-radius:10px 10px 0 0; cursor:pointer; }}
.tab[aria-selected=true] {{ background:var(--mint); color:#fff; border-color:var(--mint); }}
main {{ padding:6px 20px 40px; }}
.hud {{ font-family:var(--mono); font-size:11px; letter-spacing:.14em; color:var(--mint); opacity:.85; display:block; margin-bottom:2px; }}
.intro {{ background:linear-gradient(90deg, #e6f7f1, #fff); border:1px solid var(--line2); border-radius:14px;
  padding:10px 16px; margin:14px 0 4px; position:relative; }}
.intro h2 {{ font-size:17px; margin:0 0 3px; line-height:1.4; }}
.intro p {{ margin:0; font-size:13px; line-height:1.7; color:#33433f; }} .intro b {{ color:var(--amber); }}
.lead {{ margin:12px 0 6px; color:var(--sub); font-size:12px; }} .lead b {{ color:var(--mint-soft); }}
.fbar {{ position:sticky; top:0; z-index:50; background:rgba(255,255,255,.94); backdrop-filter:blur(6px);
  border-bottom:1px solid var(--line); box-shadow:0 4px 14px rgba(20,60,50,.08); transition:background .2s, border-color .2s; }}
.fbar.active {{ background:rgba(230,247,241,.96); border-bottom:2px solid var(--mint); }}
.bar {{ max-width:1180px; margin:0 auto; padding:8px 20px; display:flex; flex-wrap:wrap; gap:6px; align-items:center; }}
.fstate {{ font-size:12px; font-weight:800; color:var(--mint-soft); display:inline-flex; align-items:center; gap:6px; margin-left:6px; }}
.fstate button {{ font:inherit; font-size:11px; font-weight:700; border:1px solid var(--mint); color:var(--mint); background:#fff; border-radius:999px; padding:1px 9px; cursor:pointer; }}
.gempty {{ color:var(--sub); font-size:13px; margin:4px 0 0; }}
@media (max-width:640px) {{ .bar {{ flex-wrap:nowrap; overflow-x:auto; padding:7px 12px; scrollbar-width:none; }}
  .bar::-webkit-scrollbar {{ display:none; }} .f, .fe, select {{ flex:none; }} }}
.f, .fe, select {{ border:1px solid var(--line2); background:#fff; border-radius:999px; padding:4px 13px;
  font:inherit; font-size:13px; cursor:pointer; color:var(--ink); transition:all .15s; }}
.f:hover, .fe:hover {{ border-color:var(--mint); color:var(--mint); }}
.f.on {{ background:var(--mint); color:#fff; border-color:var(--mint); font-weight:700; box-shadow:0 2px 8px rgba(16,163,122,.3); }}
.fe.on {{ background:var(--sky); color:#fff; border-color:var(--sky); font-weight:700; box-shadow:0 2px 8px rgba(43,143,214,.3); }}
.sep {{ width:1px; height:20px; background:var(--line2); margin:0 4px; }}
select {{ margin-left:auto; }} 
.stampline {{ font-family:var(--mono); font-size:11px; color:var(--sub); margin:0 0 10px; letter-spacing:.02em; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(168px,1fr)); gap:10px; }}
.card {{ position:relative; background:#fff; border:1px solid var(--line); box-shadow:0 1px 3px rgba(20,60,50,.06); border-radius:12px;
  overflow:hidden; display:flex; flex-direction:column; text-decoration:none; color:inherit; }}
.card::before, .card::after {{ content:""; position:absolute; width:12px; height:12px; border:2px solid var(--mint); opacity:.55; pointer-events:none; z-index:2; }}
.card::before {{ right:5px; bottom:5px; border-left:none; border-top:none; border-radius:0 0 6px 0; }}
.card::after {{ left:5px; bottom:5px; border-right:none; border-top:none; border-radius:0 0 0 6px; }}
.card {{ transition:transform .18s cubic-bezier(.2,.8,.3,1.2), box-shadow .18s, border-color .18s; transform-origin:center bottom; }}
.card:hover {{ border-color:var(--mint); box-shadow:0 0 0 1px rgba(16,163,122,.3), 0 14px 30px rgba(16,163,122,.22); transform:scale(1.12); z-index:5; }}
@media (hover:none) {{ .card:hover {{ transform:none; }} }}
.thumb {{ position:relative; aspect-ratio:1/1; margin:0; background:#fff; overflow:hidden; border-bottom:1px solid #eef3f1; }}
.thumb img {{ width:100%; height:100%; object-fit:contain; display:block; }}
.noimg {{ display:grid; place-items:center; height:100%; color:#9aa; font-size:12px; letter-spacing:.1em; }}
.badge {{ position:absolute; left:0; top:0; background:linear-gradient(180deg,#ff3b2f,#d81f17); color:#fff; border-radius:0 0 10px 0; padding:3px 7px 3px 6px;
  line-height:1.05; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,.25); }}
.badge-l {{ display:block; font-size:8px; font-weight:800; letter-spacing:.02em; }}
.badge-n {{ display:block; font-family:var(--mono); font-size:18px; font-weight:800; letter-spacing:-.01em; }}
.badge-even {{ background:linear-gradient(180deg,#14b386,#0e936c); color:#fff; }} .badge-even .badge-n {{ font-family:inherit; font-size:13px; font-weight:800; padding:2px 1px; }}
.tags {{ position:absolute; right:5px; bottom:5px; display:flex; gap:3px; }}
.tg {{ font-size:10px; font-weight:800; border-radius:6px; padding:2px 6px; }}
.tg-half {{ background:#ffd600; color:#2a1d00; font-size:11px; box-shadow:0 1px 4px rgba(0,0,0,.2); }}
.meta s {{ font-family:var(--mono); font-weight:700; }}
.tg-new {{ background:var(--alert); color:#fff; }} .tg-re {{ background:var(--sky); color:#fff; }}
.body {{ padding:7px 10px 12px; display:flex; flex-direction:column; gap:1px; flex:1; }}
.body h3 {{ font-size:12px; line-height:1.4; margin:0; font-weight:700; display:-webkit-box; -webkit-line-clamp:2;
  -webkit-box-orient:vertical; overflow:hidden; min-height:2.8em; color:var(--ink); }}
.price {{ font-family:var(--mono); font-size:26px; font-weight:800; color:var(--ink); margin:auto 0 2px; letter-spacing:-.01em; line-height:1.1; text-align:center; }}
.price .yen {{ font-size:.6em; margin-right:1px; }}
.meta {{ font-size:11px; color:var(--sub); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; text-align:center; }}
.empty {{ color:var(--sub); }}

.corner {{ margin:22px 0 0; }}
.chead {{ margin:0 0 10px; }}
.chead .hud {{ font-size:11px; }}
.chead h2 {{ font-size:22px; margin:0; line-height:1.35; color:#0d2147; }}
.clead {{ margin:2px 0 0; font-size:12px; color:var(--sub); }} .clead b {{ color:var(--mint-soft); }}
.corner-resale {{ background:#fff; border:1px solid #c7d6e6; border-radius:16px; padding:14px 16px 10px; }}
.corner-resale .chead h2 {{ color:#0d2147; }}
.more {{ margin:12px 0 2px; }}
.more summary {{ cursor:pointer; font-size:13px; font-weight:700; color:#0d2147; padding:6px 0; }}
.tg-big {{ background:#fff; color:var(--sale); border:1px solid var(--sale); font-size:10px; }}
.newbox {{ background:#fff5f4; border:1px solid rgba(255,111,97,.5); border-radius:14px; padding:14px; margin:14px 0 6px; }}
.newbox h2 {{ margin:0 0 10px; font-size:16px; color:var(--alert); }} .newbox h2 small {{ color:var(--sub); font-weight:400; font-size:12px; }}
.rq {{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:16px 18px 8px; margin:16px 0; }}
.rq h3 {{ margin:0 0 4px; font-size:17px; }} .rq h3 small {{ color:var(--sub); font-weight:400; font-size:12px; }}
.src {{ font-size:11px; color:var(--sub); margin:0 0 10px; }} .src a {{ color:var(--sky); }}
.rt {{ width:100%; border-collapse:collapse; font-size:13px; }}
.rt th {{ text-align:left; font-size:11px; color:var(--mint); border-bottom:1px solid var(--line2); padding:6px 8px; font-family:var(--mono); letter-spacing:.06em; }}
.rt td {{ border-bottom:1px solid var(--line); padding:8px; vertical-align:middle; }}
.rp {{ white-space:nowrap; font-family:var(--mono); font-size:15px; color:var(--ink); }} .rp small {{ display:block; color:var(--sub); font-size:11px; }}
.status {{ display:inline-block; font-size:12px; border-radius:8px; padding:3px 10px; text-decoration:none; }}
.status small {{ font-size:10px; margin-left:4px; opacity:.8; }}
.ok {{ background:#e3f6ef; color:var(--mint); border:1px solid var(--line2); font-weight:700; }}
.wait {{ background:#f0f4f3; color:var(--sub); }}
.pred {{ border-color:#a9d4f2; }}
.pgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:10px; margin-bottom:10px; }}
.pday {{ background:#f6faf9; border:1px solid var(--line); border-radius:10px; padding:10px 14px; }}
.pdate {{ font-weight:800; margin-bottom:4px; }} .pday ul {{ margin:0; padding-left:18px; font-size:13px; }} .pday li {{ margin:3px 0; }}
.pk {{ font-size:10px; border-radius:999px; padding:1px 8px; margin-left:6px; font-weight:700; vertical-align:2px; }}
.pk-pred {{ background:#e1f0fb; color:var(--sky); }} .pk-pb {{ background:#fdeee0; color:#b8641a; }}
.pwide {{ grid-column:1/-1; }} .cols {{ columns:3 220px; }} .pk-real {{ background:#e3f6ef; color:var(--mint); }}
.about {{ background:linear-gradient(135deg, #e8f8f2, #eef6fd); border:1px solid var(--line2); border-radius:16px;
  padding:22px 26px; margin-top:28px; font-size:14px; position:relative; overflow:hidden; }}
.about h2 {{ font-family:var(--mono); font-size:12px; margin:0 0 6px; color:var(--mint); font-weight:400; letter-spacing:.14em; }}
.about-lead {{ font-size:22px; font-weight:800; margin:0 0 8px; color:var(--ink); }}
.about p {{ margin:6px 0; line-height:1.85; color:#33433f; }}
.sample {{ background:#fff7ec; border:1px solid #ffd2a8; color:#8a5a1f; padding:6px 12px; border-radius:8px; margin:10px 0 0; font-size:11px; }}
footer {{ border-top:1px solid var(--line); background:#fff; padding:18px 20px; font-size:11px; color:var(--sub); }}
footer p {{ margin:4px 0; }}
[hidden] {{ display:none !important; }}
@media (max-width:560px) {{
 .grid {{ grid-template-columns:repeat(3,1fr); gap:6px; }}
  .badge-n {{ font-size:13px; }} .badge-l {{ font-size:7px; }} .price {{ font-size:18px; }} .meta {{ font-size:10px; white-space:normal; }}
  select {{ margin-left:0; }} .about-lead {{ font-size:18px; }} .card::before, .card::after {{ width:8px; height:8px; }}
  .rt th:nth-child(2), .rt td.rp {{ white-space:normal; }}
}}
</style>
</head>
<body>
<div class="pr">本ページはプロモーション（Amazonアソシエイト）を含みます</div>
<header><div class="hwrap">
  <div class="brand">
    <h1 class="logo"><img src="{LOGO_URI}" alt="{SITE_NAME}"></h1>
    <span class="vsep hide-sm"></span>
    <div class="sys hide-md"><div><span class="anti">ANTI TENBUYER</span><br>GUM-PLA DISTRIBUTION SYSTEM</div>
      <svg width="64" height="40" viewBox="0 0 64 40" aria-hidden="true"><rect x="2" y="16" width="8" height="8" fill="#10a37a"/>
      <path d="M10 20 H22 M22 20 L34 8 H46 M22 20 H46 M22 20 L34 32 H46" stroke="#0d2147" stroke-width="1.6" fill="none"/>
      <rect x="46" y="4" width="8" height="8" fill="#fff" stroke="#0d2147" stroke-width="1.6"/><rect x="46" y="16" width="8" height="8" fill="#fff" stroke="#0d2147" stroke-width="1.6"/>
      <rect x="46" y="28" width="8" height="8" fill="#fff" stroke="#0d2147" stroke-width="1.6"/></svg></div>
    <span class="vsep hide-md"></span>
    <div class="online"><span class="sq"></span>ONLINE<small>毎日更新</small></div>
  </div>
  <p class="tag">{SITE_TAGLINE_HTML}</p>
</div></header>
<nav class="fbar" aria-label="絞り込みと並べ替え"><div class="bar">
    <button class="f on" data-g="ALL">すべて</button>{grade_btns}
    <span class="sep"></span>
    <button class="fe on" data-e="ALL">全シリーズ</button><button class="fe" data-e="宇宙世紀">宇宙世紀</button><button class="fe" data-e="アナザー">アナザー</button><button class="fe" data-e="SD・その他">SD・その他</button>
    <span class="fstate" id="fstate" hidden>絞り込み中 <button type="button" id="freset">解除</button></span>
    <select id="sort" aria-label="並び替え">
      <option value="off">お得な順</option>
      <option value="price">価格が安い順</option>
    </select>
</div></nav>
<main>
<section class="intro">
  <span class="hud">MESSAGE</span>
  <h2>今でも、ガンプラは安く買えます。――ほら！</h2>
  <p>「転売ヤーのせいで高い」と思われがちですが、<b>転売相場の半額以下</b>や<b>定価より安い</b>ガンプラは、まだまだあります。転売ヤーが一番困るのは、みんなが高い転売品に手を出さず、定価や安い値段のガンプラをどんどん買うこと。転売ヤーの言い値で買わずに済むガンプラだけを、毎日まとめています。</p>
</section>
<section class="corner corner-resale">
  <div class="chead"><span class="hud">RESALE ／ 再販情報</span>
    <h2>最新再販ガンプラ情報</h2>
    <p class="clead">バンダイ公式の再販リストとファンサイトの再販報告のうち、Amazonで定価以下・定価並みで買える商品です。{f"NEWは今日からAmazon本体で買えるようになった商品。" if new_items else ""}</p></div>
  <div class="grid grid-feat">{featured_html}</div>
  <details class="more">
    <summary>再販予想・入荷報告・プレバン再販／公式再販リストを見る</summary>
    {predictions_html(pred, fair)}
    {"".join(resale_html)}
  </details>
</section>
<section class="corner" id="fair">
  <div class="chead"><span class="hud">SALE ／ 値下げ中</span>
    <h2>今が買い時！ 値下げ中のガンプラ</h2>
    <p class="clead"><b>Amazon.co.jp本体の販売</b>か、<b>定価＋5%以内</b>で新品が買えるものだけ。転売相場の半額以下や、定価から大幅値下げ中のものも。毎日更新。</p></div>
  <div class="stampline">価格・在庫は {e(stamp)} 時点のものです。購入時はAmazon.co.jpに表示される価格が適用されます。</div>
  <div class="grid" id="grid">{cards}</div>
</section>
<section class="about">
  <h2>WHY WE MADE THIS ／ このサイトを作った理由</h2>
  <p class="about-lead">転売ヤーを、ガンプラの世界からなくしたい。</p>
  <p>でも、転売ヤーを責めたり攻撃したりしても、きっと何も変わりません。だったら、正規の値段で、できればもっと安く買える場所を、誰にでもわかるように示せばいい。みんなが安く買えば買うほど、高値で売りつけようとする転売ヤーは困ります。</p>
  <p>{SITE_NAME}は、そのためのお得なガンプラ情報を、ファンみんなで共有するために作りました。欲しかったあのキット、定価で手に入るかもしれません。</p>
</section>
{sample_banner}
</main>
<footer><div class="fwrap">
  <p>※「転売相場」は、Amazonマーケットプレイスやメルカリなどでの出品を調べて算出した概算です。すべてが転売ヤーによる出品とは限りません（中古品などを含む場合があります）。</p>
  <p>価格と在庫は表示時点のもので、変わることがあります。購入時にAmazon.co.jpに表示される価格と在庫が適用されます。</p>
  <p>本サイトに表示されるコンテンツの一部はAmazonから提供されています。このコンテンツは「現状のまま」提供され、随時変更または削除される場合があります。<br>CERTAIN CONTENT THAT APPEARS ON THIS SITE COMES FROM AMAZON. THIS CONTENT IS PROVIDED 'AS IS' AND IS SUBJECT TO CHANGE OR REMOVAL AT ANY TIME.</p>
  <p>Amazonのアソシエイトとして、{SITE_NAME}は適格販売により収入を得ています。</p>
  <p>再販情報の出典：株式会社BANDAI SPIRITS バンダイ ホビーサイト。当サイトはBANDAI SPIRITSおよびAmazonとは関係のない個人運営サイトです。</p>
</div></footer>
<script>
(() => {{
  const grids = [...document.querySelectorAll('.grid')];
  const bar = document.querySelector('.fbar'), state = document.getElementById('fstate');
  let g = 'ALL', era = 'ALL';
  const apply = () => {{
    grids.forEach(grid => {{
      let shown = 0;
      grid.querySelectorAll('.card').forEach(c => {{
        c.hidden = (g !== 'ALL' && c.dataset.grade !== g) || (era !== 'ALL' && c.dataset.era !== era);
        if (!c.hidden) shown++;
      }});
      let m = grid.querySelector('.gempty');
      if (!shown && grid.querySelector('.card')) {{
        if (!m) {{ m = document.createElement('p'); m.className = 'gempty'; m.textContent = 'この条件に合う商品はありません。'; grid.appendChild(m); }}
      }} else if (m) m.remove();
    }});
    const on = g !== 'ALL' || era !== 'ALL';
    bar.classList.toggle('active', on); state.hidden = !on;
  }};
  const btns = document.querySelectorAll('.f');
  const setG = v => {{ g = v; btns.forEach(x => x.classList.toggle('on', x.dataset.g === v)); }};
  btns.forEach(b => b.addEventListener('click', () => {{ setG(b.dataset.g); apply(); }}));
  const ebtns = document.querySelectorAll('.fe');
  const setE = v => {{ era = v; ebtns.forEach(x => x.classList.toggle('on', x.dataset.e === v)); }};
  ebtns.forEach(b => b.addEventListener('click', () => {{ setE(b.dataset.e); apply(); }}));
  document.getElementById('freset').addEventListener('click', () => {{ setG('ALL'); setE('ALL'); apply(); }});
  document.getElementById('sort').addEventListener('change', ev => {{
    const k = ev.target.value;
    grids.forEach(grid => [...grid.querySelectorAll('.card')].sort((a, b) => k === 'off'
      ? (b.dataset.off - a.dataset.off) || (a.dataset.price - b.dataset.price)
      : (a.dataset.price - b.dataset.price)).forEach(c => grid.appendChild(c)));
  }});
}})();
</script>
</body>
</html>'''
