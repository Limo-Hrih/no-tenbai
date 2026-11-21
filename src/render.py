"""静的HTMLを1枚生成する。"""
from __future__ import annotations

import html
import re
from datetime import datetime

from select_items import Product

SITE_NAME = "NO転売ガンプラ市場"
SITE_TAGLINE = "転売価格はNo！ 正規の値段で買えるガンプラ情報だけを毎日まとめています。"
SITE_TAGLINE_HTML = "転売価格はNo！ 正規の値段で買えるガンプラ情報だけを毎日まとめています。"

GRADES = ["HG", "RG", "MG", "PG", "EG", "SD", "その他"]


def grade_of(title: str) -> str:
    t = title.upper()
    for g, pat in [("PG", r"\bPG\b|PERFECT GRADE"), ("MG", r"\bMG\b|MASTER GRADE"),
                   ("RG", r"\bRG\b|REAL GRADE"), ("EG", r"\bEG\b|ENTRY GRADE"),
                   ("HG", r"\bHG|HIGH GRADE"), ("SD", r"\bSD\b|BB戦士|SDCS|SDEX")]:
        if re.search(pat, t):
            return g
    return "その他"


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
    if any(k in t for k in ("三国創傑伝", "SDW HEROES", "ガンプラくん")):
        return "その他"
    if any(k in t for k in ANOTHER_KEYS):
        return "アナザー"
    if any(k in t for k in UC_KEYS):
        return "宇宙世紀"
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
        badge = f'<div class="badge"><span class="badge-l">転売相場より</span><span class="badge-n">−{moff}%</span></div>'
    elif off is not None and off > 0:
        badge = f'<div class="badge"><span class="badge-l">定価より</span><span class="badge-n">−{off}%</span></div>'
    elif p.list_price:
        badge = '<div class="badge badge-even"><span class="badge-n">定価</span></div>'
    else:
        badge = '<div class="badge badge-even"><span class="badge-n">正規販売</span></div>'
    img = f'<img src="{e(p.image)}" alt="" loading="lazy">' if p.image else '<div class="noimg">NO IMAGE</div>'
    tags = ""
    if p.is_new:
        tags += '<span class="tg tg-new">NEW</span>'
    if p.resale_quarter:
        tags += '<span class="tg tg-re">再販</span>'
    meta = []
    if p.list_price:
        meta.append(f"希望価格 {yen(p.list_price)}")
    if moff is not None and moff >= 10:
        meta.append(f"転売相場 {yen(p.market_low)}")
    meta_html = "".join(f'<div class="meta">{m}</div>' for m in meta)
    return f'''
<a class="card" href="{e(p.url)}" target="_blank" rel="sponsored noopener" data-grade="{e(grade_of(p.title))}" data-era="{e(era_of(p.title))}" data-off="{max(off or 0, moff or 0)}" data-price="{b.price}">
  <div class="thumb">{img}{badge}{f'<div class="tags">{tags}</div>' if tags else ''}</div>
  <div class="body">
    <h3 title="{e(p.title)}">{e(short_title(p.title))}</h3>
    <div class="price">{yen(b.price)}</div>
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
header {{ background:var(--ink); color:#fff; padding:16px 20px 0; }}
.hwrap, main, footer .fwrap {{ max-width:1120px; margin:0 auto; }}
.logo {{ font-size:22px; font-weight:800; letter-spacing:.04em; margin:0; }}
.logo span {{ display:inline-block; width:10px; height:24px; margin-right:4px; vertical-align:-3px; }}
.logo .b {{ background:var(--blue); }} .logo .r {{ background:var(--red); }} .logo .y {{ background:var(--yellow); margin-right:12px; }}
.tag {{ margin:2px 0 0; color:#c9d1e0; font-size:13px; }}
.tabs {{ display:flex; gap:4px; margin-top:12px; }}
.tab {{ border:0; background:transparent; color:#c9d1e0; font:inherit; font-weight:700; font-size:15px;
  padding:8px 16px; border-radius:10px 10px 0 0; cursor:pointer; }}
.tab[aria-selected=true] {{ background:var(--bg); color:var(--ink); }}
.intro {{ background:#fff; border:1px solid var(--line); border-left:6px solid var(--red); border-radius:14px;
  padding:10px 16px; margin:14px 0 4px; }}
.intro h2 {{ font-size:16px; margin:0 0 3px; line-height:1.4; }}
.intro p {{ margin:0; font-size:13px; line-height:1.6; }} .intro b {{ color:var(--red); }}
.sample {{ background:#fff4d6; border:1px solid var(--yellow); color:#6b4e00; padding:6px 12px;
  border-radius:8px; margin:8px 0 0; font-size:12px; }}
main {{ padding:8px 20px 40px; }}
.lead {{ margin:10px 0 6px; color:var(--sub); font-size:12px; }}
.lead b {{ color:var(--ink); }}
.bar {{ display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin:4px 0 14px; }}
.f, select {{ border:1px solid var(--line); background:#fff; border-radius:999px; padding:4px 12px;
  font:inherit; font-size:13px; cursor:pointer; color:var(--ink); }}
.fe {{ border:1px solid var(--line); background:#fff; border-radius:999px; padding:4px 12px; font:inherit; font-size:13px; cursor:pointer; color:var(--ink); }}
.fe.on {{ background:var(--blue); color:#fff; border-color:var(--blue); }}
.sep {{ width:1px; height:20px; background:var(--line); margin:0 4px; }}
.f.on {{ background:var(--ink); color:#fff; border-color:var(--ink); }}
select {{ margin-left:auto; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(168px,1fr)); gap:10px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; overflow:hidden;
  display:flex; flex-direction:column; text-decoration:none; color:inherit; transition:box-shadow .15s, transform .15s; }}
.card:hover {{ box-shadow:0 4px 14px rgba(0,0,0,.12); transform:translateY(-1px); }}
.thumb {{ position:relative; aspect-ratio:1/1; background:#fff; }}
.thumb img {{ width:100%; height:100%; object-fit:contain; display:block; }}
.noimg {{ display:grid; place-items:center; height:100%; color:#b8c0cc; font-size:12px; letter-spacing:.1em; }}
.badge {{ position:absolute; left:6px; top:6px; background:var(--red); color:#fff; border-radius:8px;
  padding:4px 7px 3px; line-height:1.05; text-align:center; box-shadow:0 2px 5px rgba(0,0,0,.18); }}
.badge-l {{ display:block; font-size:9px; font-weight:700; opacity:.92; }}
.badge-n {{ display:block; font-size:19px; font-weight:800; }}
.badge-even {{ background:var(--blue); }} .badge-even .badge-n {{ font-size:14px; padding:2px 1px; }}
.tags {{ position:absolute; right:6px; top:6px; display:flex; gap:3px; }}
.tg {{ font-size:10px; font-weight:800; border-radius:6px; padding:2px 6px; color:#fff; }}
.tg-new {{ background:var(--red); }} .tg-re {{ background:var(--blue); }}
.body {{ padding:7px 9px 9px; display:flex; flex-direction:column; gap:2px; flex:1; }}
.body h3 {{ font-size:12px; line-height:1.35; margin:0; font-weight:600; display:-webkit-box;
  -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; min-height:2.7em; }}
.price {{ font-size:18px; font-weight:800; margin-top:auto; }}
.meta {{ font-size:11px; color:var(--sub); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.stampline {{ font-size:12px; color:var(--sub); margin:-8px 0 10px; }}
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
.about {{ background:#fff; border:1px solid var(--line); border-left:6px solid var(--blue); border-radius:14px; padding:20px 24px; margin-top:28px; font-size:14px; }}
.about h2 {{ font-size:13px; margin:0 0 6px; color:var(--sub); font-weight:700; letter-spacing:.05em; }}
.about-lead {{ font-size:20px; font-weight:800; margin:0 0 8px; color:var(--ink); }}
.about p {{ margin:6px 0; line-height:1.8; }}
footer {{ border-top:1px solid var(--line); background:#fff; padding:20px; font-size:12px; color:var(--sub); }}
footer p {{ margin:4px 0; }}
[hidden] {{ display:none !important; }}
@media (max-width:560px) {{
  .logo {{ font-size:22px; }} .grid {{ grid-template-columns:repeat(3,1fr); gap:6px; }}
  .badge-n {{ font-size:15px; }} .price {{ font-size:15px; }} .meta {{ font-size:10px; white-space:normal; }} select {{ margin-left:0; }}
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
<section class="intro">
  <h2>今でも、ガンプラは安く買えます。――ほら！</h2>
  <p>「転売ヤーのせいで高い」と思われがちですが、<b>転売相場の半額以下</b>や<b>定価より安い</b>ガンプラは、まだまだあります。転売ヤーが一番困るのは、みんなが高い転売品に手を出さず、定価や安い値段のガンプラをどんどん買うこと。転売ヤーの言い値で買わずに済むガンプラだけを、毎日まとめています。</p>
</section>
<section id="fair">
  {new_html}
  <p class="lead"><b>Amazon.co.jp本体の販売</b>か、<b>定価＋5%以内</b>で新品が買えるものだけを載せています。毎日更新。</p>
  <div class="bar">
    <button class="f on" data-g="ALL">すべて</button>{grade_btns}
    <span class="sep"></span>
    <button class="fe on" data-e="ALL">全シリーズ</button><button class="fe" data-e="宇宙世紀">宇宙世紀</button><button class="fe" data-e="アナザー">アナザー</button>
    <select id="sort" aria-label="並び替え">
      <option value="off">お得な順</option>
      <option value="price">価格が安い順</option>
    </select>
  </div>
  <div class="stampline">価格・在庫は {e(stamp)} 時点のものです。購入時はAmazon.co.jpに表示される価格が適用されます。</div>
  <div class="grid" id="grid">{cards}</div>
</section>
<section id="resale" hidden>
  <p class="lead">今週の再販予想と、バンダイ公式が発表している今期の再販商品です。<b>Amazonで定価以下・定価に近い値段で買えるもの</b>にだけリンクを付けています。</p>
  {predictions_html(pred, fair)}
  {"".join(resale_html)}
</section>
<section class="about">
  <h2>このサイトを作った理由</h2>
  <p class="about-lead">転売ヤーを、ガンプラの世界からなくしたい。</p>
  <p>でも、転売ヤーを責めたり攻撃したりしても、きっと何も変わりません。だったら、正規の値段で、できればもっと安く買える場所を、誰にでもわかるように示せばいい。みんなが安く買えば買うほど、高値で売りつけようとする転売ヤーは困ります。</p>
  <p>NO転売ガンプラ市場は、そのためのお得なガンプラ情報を、ファンみんなで共有するために作りました。欲しかったあのキット、定価で手に入るかもしれません。</p>
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
  const tabs = document.querySelectorAll('.tab');
  tabs.forEach(t => t.addEventListener('click', () => {{
    tabs.forEach(x => x.setAttribute('aria-selected', x === t));
    document.getElementById('fair').hidden = t.dataset.t !== 'fair';
    document.getElementById('resale').hidden = t.dataset.t !== 'resale';
  }}));
  const grid = document.getElementById('grid');
  let g = 'ALL', era = 'ALL';
  const apply = () => grid.querySelectorAll('.card').forEach(c => {{
    c.hidden = (g !== 'ALL' && c.dataset.grade !== g) || (era !== 'ALL' && c.dataset.era !== era);
  }});
  const btns = document.querySelectorAll('.f');
  btns.forEach(b => b.addEventListener('click', () => {{
    btns.forEach(x => x.classList.toggle('on', x === b)); g = b.dataset.g; apply();
  }}));
  const ebtns = document.querySelectorAll('.fe');
  ebtns.forEach(b => b.addEventListener('click', () => {{
    ebtns.forEach(x => x.classList.toggle('on', x === b)); era = b.dataset.e; apply();
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
