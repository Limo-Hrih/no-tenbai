"""静的HTMLを1枚生成する。"""
from __future__ import annotations

import html
import re
from datetime import datetime

from select_items import Product

SITE_NAME = "定価でガンプラ"
SITE_TAGLINE = "転売価格はNo！ 正規の値段で買えるガンプラ情報だけを毎日まとめています。"
SITE_TAGLINE_HTML = "転売価格はNo！<br>正規の値段で買えるガンプラ情報だけを毎日まとめています。"

GRADES = ["HG", "RG", "MG", "PG", "EG", "SD", "その他"]


def grade_of(title: str) -> str:
    t = title.upper()
    for g, pat in [("PG", r"\bPG\b|PERFECT GRADE"), ("MG", r"\bMG\b|MASTER GRADE"),
                   ("RG", r"\bRG\b|REAL GRADE"), ("EG", r"\bEG\b|ENTRY GRADE"),
                   ("HG", r"\bHG|HIGH GRADE"), ("SD", r"\bSD\b|BB戦士|SDCS|SDEX")]:
        if re.search(pat, t):
            return g
    return "その他"


def yen(n: int | None) -> str:
    return "—" if n is None else f"¥{n:,}"


def e(s) -> str:
    return html.escape(str(s), quote=True)


def card(p: Product, stamp: str) -> str:
    b = p.best
    off = p.off_pct
    moff = p.market_off_pct
    if moff is not None and moff >= 10 and moff >= (off or 0):
        badge = f'<div class="badge"><span class="badge-l">マケプレより</span><span class="badge-n">−{moff}%</span></div>'
    elif off is not None and off > 0:
        badge = f'<div class="badge"><span class="badge-l">定価比</span><span class="badge-n">−{off}%</span></div>'
    elif off is not None:
        badge = '<div class="badge badge-even"><span class="badge-l">定価</span><span class="badge-n">ほぼ定価</span></div>'
    else:
        badge = '<div class="badge badge-even"><span class="badge-l">Amazon</span><span class="badge-n">本体販売</span></div>'
    lp_label = "メーカー希望小売価格" if p.list_price_source == "official" else "参考価格"
    seller = '<span class="chip chip-amz">Amazon.co.jp が販売</span>' if b.is_amazon \
        else '<span class="chip">定価に近いマーケットプレイス出品</span>'
    pts = f'<span class="pts">{b.points:,}pt</span>' if b.points else ""
    img = f'<img src="{e(p.image)}" alt="" loading="lazy">' if p.image else '<div class="noimg">NO IMAGE</div>'
    resale = f'<span class="chip chip-resale">{e(p.resale_quarter)} 公式再販</span>' if p.resale_quarter else ""
    if p.is_new:
        resale = '<span class="chip chip-new">NEW 今日から</span>' + resale
    return f'''
<article class="card" data-grade="{e(grade_of(p.title))}" data-off="{max(off or 0, moff or 0)}" data-price="{b.price}">
  <a class="thumb" href="{e(p.url)}" target="_blank" rel="sponsored noopener">{img}{badge}</a>
  <div class="body">
    <h3><a href="{e(p.url)}" target="_blank" rel="sponsored noopener">{e(p.title)}</a></h3>
    <div class="chips">{seller}{resale}</div>
    <div class="price-row">
      <span class="price">{yen(b.price)}</span>{pts}
    </div>
    <div class="lp">{lp_label} {yen(p.list_price)}{f'（定価比 −{off}%）' if off and off > 0 else ''}</div>
    {f'<div class="lp">マケプレ相場（概算）{yen(p.market_low)}<sup>※</sup></div>' if moff is not None and moff >= 10 else ''}
    <div class="stamp">価格・在庫は {e(stamp)} 時点</div>
    <a class="btn" href="{e(p.url)}" target="_blank" rel="sponsored noopener">Amazonで見る</a>
  </div>
</article>'''


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


def predictions_html(pred: dict | None, fair: list[Product]) -> str:
    if not pred:
        return ""
    fair_by_title = {p.title: p for p in fair}
    days = []
    for d in pred["days"]:
        lis = []
        for name in d["items"]:
            key = _norm(name.split("（")[0])
            hit = next((p for t, p in fair_by_title.items() if key and key in _norm(t)), None)
            tail = (f' <a class="status ok" href="{e(hit.url)}" target="_blank" rel="sponsored noopener">'
                    f'{buy_label(hit)}</a>') if hit else ""
            lis.append(f"<li>{e(name)}{tail}</li>")
        cls = "pk-pred" if d["kind"] == "予測" else "pk-real"
        days.append(f'''<div class="pday"><div class="pdate">{e(d["date"])}
  <span class="pk {cls}">{e(d["kind"])}</span></div><ul>{"".join(lis)}</ul></div>''')
    srcs = "・".join(f'<a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["name"])}</a>'
                    for s in pred["sources"])
    return f'''
<section class="rq pred">
  <h3>今週の再販予想・入荷報告 <small>{e(pred["week"])}</small></h3>
  <p class="src">{e(pred["note"])}<br>出典：{srcs}</p>
  <div class="pgrid">{"".join(days)}</div>
</section>'''


def render(fair: list[Product], resale_groups: list[dict], generated_at: datetime,
           sample: bool = False, pred: dict | None = None, snapshot: bool = False) -> str:
    stamp = generated_at.strftime("%Y/%m/%d %H:%M")
    fair_by_asin = {p.asin: p for p in fair}
    cards = "\n".join(card(p, stamp) for p in fair) or '<p class="empty">いま該当する商品はありません。</p>'
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
<style>
:root {{
  --ink:#1b2230; --sub:#5d6778; --line:#e3e7ee; --bg:#f6f7fa; --card:#fff;
  --blue:#1f4fa3; --red:#d6372b; --yellow:#f3b61f; --green:#13866f;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:"Hiragino Sans","Noto Sans JP","Yu Gothic UI",sans-serif;
  color:var(--ink); background:var(--bg); line-height:1.6; }}
a {{ color:inherit; }}
.pr {{ background:#fff; border-bottom:1px solid var(--line); font-size:12px; color:var(--sub);
  text-align:center; padding:4px 8px; }}
header {{ background:var(--ink); color:#fff; padding:28px 20px 0; }}
.hwrap, main, footer .fwrap {{ max-width:1120px; margin:0 auto; }}
.logo {{ font-size:28px; font-weight:800; letter-spacing:.04em; margin:0; }}
.logo span {{ display:inline-block; width:10px; height:24px; margin-right:4px; vertical-align:-3px; }}
.logo .b {{ background:var(--blue); }} .logo .r {{ background:var(--red); }} .logo .y {{ background:var(--yellow); margin-right:12px; }}
.tag {{ margin:6px 0 0; color:#c9d1e0; font-size:15px; }}
.tabs {{ display:flex; gap:4px; margin-top:22px; }}
.tab {{ border:0; background:transparent; color:#c9d1e0; font:inherit; font-weight:700; font-size:15px;
  padding:12px 18px; border-radius:10px 10px 0 0; cursor:pointer; }}
.tab[aria-selected=true] {{ background:var(--bg); color:var(--ink); }}
.sample {{ background:#fff4d6; border:1px solid var(--yellow); color:#6b4e00; padding:10px 14px;
  border-radius:8px; margin:16px 0 0; font-size:14px; }}
main {{ padding:8px 20px 40px; }}
.lead {{ margin:18px 0 10px; color:var(--sub); font-size:14px; }}
.lead b {{ color:var(--ink); }}
.bar {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:8px 0 18px; }}
.f, select {{ border:1px solid var(--line); background:#fff; border-radius:999px; padding:6px 14px;
  font:inherit; font-size:14px; cursor:pointer; color:var(--ink); }}
.f.on {{ background:var(--ink); color:#fff; border-color:var(--ink); }}
select {{ margin-left:auto; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:16px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:14px; overflow:hidden;
  display:flex; flex-direction:column; }}
.thumb {{ position:relative; display:block; aspect-ratio:1/1; background:#fff; border-bottom:1px solid var(--line); }}
.thumb img {{ width:100%; height:100%; object-fit:contain; padding:14px; }}
.noimg {{ display:grid; place-items:center; height:100%; color:#b8c0cc; font-size:12px; letter-spacing:.1em; }}
.badge {{ position:absolute; left:10px; top:10px; background:var(--red); color:#fff; border-radius:10px;
  padding:6px 10px 5px; line-height:1.1; text-align:center; box-shadow:0 2px 6px rgba(0,0,0,.15); }}
.badge-even {{ background:var(--blue); }}
.badge-l {{ display:block; font-size:11px; font-weight:700; opacity:.9; }}
.badge-n {{ display:block; font-size:24px; font-weight:800; letter-spacing:.01em; }}
.badge-even .badge-n {{ font-size:16px; padding:2px 0 1px; }}
.body {{ padding:12px 14px 14px; display:flex; flex-direction:column; gap:6px; flex:1; }}
.body h3 {{ font-size:14px; line-height:1.45; margin:0; font-weight:700; }}
.body h3 a {{ text-decoration:none; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }}
.chips {{ display:flex; flex-wrap:wrap; gap:4px; }}
.chip {{ font-size:11px; border:1px solid var(--line); border-radius:999px; padding:1px 8px; color:var(--sub); }}
.chip-amz {{ border-color:var(--green); color:var(--green); font-weight:700; }}
.chip-resale {{ border-color:var(--yellow); color:#8a6300; }}
.chip-new {{ background:var(--red); border-color:var(--red); color:#fff; font-weight:800; }}
.newbox {{ background:#fff; border:2px solid var(--red); border-radius:16px; padding:16px; margin:18px 0 8px; }}
.newbox h2 {{ margin:0 0 12px; font-size:18px; color:var(--red); }}
.newbox h2 small {{ color:var(--sub); font-weight:400; font-size:13px; }}
.lp sup {{ font-size:9px; }}
.pred {{ border:2px solid var(--blue); }}
.pgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:12px; margin-bottom:10px; }}
.pday {{ background:var(--bg); border-radius:10px; padding:10px 14px; }}
.pdate {{ font-weight:800; margin-bottom:4px; }}
.pday ul {{ margin:0; padding-left:18px; font-size:14px; }} .pday li {{ margin:3px 0; }}
.pk {{ font-size:11px; border-radius:999px; padding:1px 8px; margin-left:6px; font-weight:700; vertical-align:2px; }}
.pk-pred {{ background:#e6edf9; color:var(--blue); }} .pk-real {{ background:#e3f4ef; color:var(--green); }}
.price-row {{ display:flex; align-items:baseline; gap:8px; margin-top:auto; }}
.price {{ font-size:22px; font-weight:800; }}
.pts {{ font-size:12px; color:var(--sub); }}
.lp {{ font-size:12px; color:var(--sub); }}
.stamp {{ font-size:11px; color:#8b94a3; }}
.btn {{ display:block; text-align:center; background:var(--yellow); color:#1b2230; font-weight:800;
  text-decoration:none; border-radius:10px; padding:9px; margin-top:6px; }}
.btn:hover {{ filter:brightness(.96); }}
.empty {{ color:var(--sub); }}
.rq {{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:18px 18px 8px; margin:18px 0; }}
.rq h3 {{ margin:0 0 4px; font-size:18px; }} .rq h3 small {{ color:var(--sub); font-weight:400; font-size:13px; }}
.src {{ font-size:12px; color:var(--sub); margin:0 0 10px; }}
.rt {{ width:100%; border-collapse:collapse; font-size:14px; }}
.rt th {{ text-align:left; font-size:12px; color:var(--sub); border-bottom:2px solid var(--line); padding:6px 8px; }}
.rt td {{ border-bottom:1px solid var(--line); padding:9px 8px; vertical-align:middle; }}
.rp {{ white-space:nowrap; font-weight:700; }} .rp small {{ display:block; font-weight:400; color:#8b94a3; font-size:11px; }}
.status {{ display:inline-block; font-size:13px; border-radius:8px; padding:4px 10px; text-decoration:none; }}
.status small {{ font-size:10px; margin-left:4px; opacity:.8; }}
.ok {{ background:#e3f4ef; color:var(--green); font-weight:700; }}
.wait {{ background:#f0f2f5; color:var(--sub); }}
.about {{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:18px; margin-top:28px; font-size:14px; }}
.about h2 {{ font-size:16px; margin:0 0 8px; }}
footer {{ border-top:1px solid var(--line); background:#fff; padding:20px; font-size:12px; color:var(--sub); }}
footer p {{ margin:4px 0; }}
[hidden] {{ display:none !important; }}
@media (max-width:560px) {{
  .logo {{ font-size:22px; }} .grid {{ grid-template-columns:repeat(2,1fr); gap:10px; }}
  .badge-n {{ font-size:19px; }} .price {{ font-size:18px; }} select {{ margin-left:0; }}
  .rt th:nth-child(2), .rt td.rp {{ white-space:normal; }}
}}
</style>
</head>
<body>
<div class="pr">本ページはプロモーション（Amazonアソシエイト）を含みます</div>
<header><div class="hwrap">
  <h1 class="logo"><span class="b"></span><span class="r"></span><span class="y"></span>{SITE_NAME}</h1>
  <p class="tag">{SITE_TAGLINE_HTML}</p>
  <div class="tabs" role="tablist">
    <button class="tab" role="tab" aria-selected="true" data-t="fair">いま定価で買える</button>
    <button class="tab" role="tab" aria-selected="false" data-t="resale">再販情報</button>
  </div>
</div></header>
<main>
{sample_banner}
<section id="fair">
  {new_html}
  <p class="lead"><b>Amazon.co.jp本体の販売</b>か、<b>定価＋5%以内</b>で新品が買えるものだけを載せています。転売価格の出品は載せていません。毎日更新（最終更新 {e(stamp)}）。</p>
  <div class="bar">
    <button class="f on" data-g="ALL">すべて</button>{grade_btns}
    <select id="sort" aria-label="並び替え">
      <option value="off">お得な順</option>
      <option value="price">価格が安い順</option>
    </select>
  </div>
  <div class="grid" id="grid">{cards}</div>
</section>
<section id="resale" hidden>
  <p class="lead">今週の再販予想と、バンダイ公式が発表している今期の再販商品です。<b>Amazonで定価以下・定価に近い値段で買えるもの</b>にだけリンクを付けています。</p>
  {predictions_html(pred, fair)}
  {"".join(resale_html)}
</section>
<section class="about">
  <h2>このサイトについて</h2>
  <p>人気のガンプラは、品薄になると定価より高い値段で出品されがちです。このサイトは、ファンが正規の値段で買える場所を見つけやすくするために、Amazon.co.jp本体の販売や定価に近い出品だけを毎日選んで紹介しています。紹介するのは正規の販売や定価に近い出品だけで、転売価格の出品にはリンクしません。</p>
</section>
</main>
<footer><div class="fwrap">
  <p>※「マケプレ相場」は、同じ商品のAmazonマーケットプレイス出品から求めた概算です。正確には転売価格ではなく、マーケットプレイスやフリマなどでの再販品・再販価格のため、すべてが転売目的の出品というわけではありません（中古品などを含む場合があります）。</p>
  <p>価格と在庫は表示時点のもので、変わることがあります。購入時にAmazon.co.jpに表示される価格と在庫が適用されます。</p>
  <p>本サイトに表示されるコンテンツの一部はAmazonから提供されています。このコンテンツは「現状のまま」提供され、随時変更または削除される場合があります。<br>CERTAIN CONTENT THAT APPEARS ON THIS SITE COMES FROM AMAZON. THIS CONTENT IS PROVIDED 'AS IS' AND IS SUBJECT TO CHANGE OR REMOVAL AT ANY TIME.</p>
  <p>Amazonのアソシエイトとして、{SITE_NAME}は適格販売により収入を得ています。</p>
  <p>再販情報の出典：株式会社BANDAI SPIRITS バンダイ ホビーサイト。当サイトはBANDAI SPIRITSおよびAmazonとは関係のない個人運営サイトです。</p>
</div></footer>
<script>
(() => {{
  const tabs = document.querySelectorAll('.tab');
  tabs.forEach(t => t.addEventListener('click', () => {{
    tabs.forEach(x => x.setAttribute('aria-selected', x === t));
    document.getElementById('fair').hidden = t.dataset.t !== 'fair';
    document.getElementById('resale').hidden = t.dataset.t !== 'resale';
  }}));
  const grid = document.getElementById('grid');
  const btns = document.querySelectorAll('.f');
  btns.forEach(b => b.addEventListener('click', () => {{
    btns.forEach(x => x.classList.toggle('on', x === b));
    grid.querySelectorAll('.card').forEach(c => {{
      c.hidden = b.dataset.g !== 'ALL' && c.dataset.grade !== b.dataset.g;
    }});
  }}));
  document.getElementById('sort').addEventListener('change', ev => {{
    const k = ev.target.value;
    [...grid.children].sort((a, b) => k === 'off'
      ? (b.dataset.off - a.dataset.off) || (a.dataset.price - b.dataset.price)
      : (a.dataset.price - b.dataset.price)).forEach(c => grid.appendChild(c));
  }});
}})();
</script>
</body>
</html>'''
