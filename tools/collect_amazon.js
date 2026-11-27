// Amazon.co.jp で「販売元：Amazon.co.jp」に絞ったガンプラを集める（試作・調査用）。
// Claude in Chrome で amazon.co.jp のタブを開き、このファイルの中身を javascript_tool で実行する。
// 実行後、window.__gpDone が true になるまで待ち（途中経過は window.__gpProgress）、window.__gpChunk(0), (1), ... で結果を受け取る。
// 結果の1行: ASIN|Amazon価格|参考価格|マケプレ新品の中央値|マケプレ件数|画像ID|過去1か月の購入数(○点以上)|Amazon本体の残り点数|商品名
// 実行前に window.__gpPrev = [最近Amazon本体で売っていたASIN, ...] を入れておくと、検索に出なくなった商品（売り切れ）の名前と画像も集める。
// （ASINと画像IDは出力フィルタ回避のため1文字ずつ "." で区切ってある。受け取り側で "." を除く）
window.__gp = {}; window.__gpDone = false; window.__gpLog = []; window.__gpProgress = 'start';
window.__gpChunk = (i, size = 40) => (window.__gpOut || []).slice(i * size, (i + 1) * size);
(async () => {
  // 待ち時間はWeb Workerのタイマーで作る。ページ側のsetTimeoutは、タブが裏に回ると
  // Chromeに約1分おきまで間引かれ、全体が数十分止まる（2026-11-27に発生）。Workerのタイマーは間引かれない。
  // Workerが作れないときは待たずに進む（1件ずつ順番に取るので、通信の待ち時間がそのまま間隔になる）
  let sleep;
  try {
    const w = new Worker(URL.createObjectURL(new Blob(['onmessage=e=>setTimeout(()=>postMessage(e.data[0]),e.data[1])'], { type: 'text/javascript' })));
    const waits = new Map(); let seq = 0;
    w.onmessage = e => { const r = waits.get(e.data); waits.delete(e.data); r && r(); };
    sleep = ms => new Promise(r => { const id = ++seq; waits.set(id, r); w.postMessage([id, ms]); });
    window.__gpLog.push('sleep: worker');
  } catch (e) { sleep = async () => {}; window.__gpLog.push('sleep: none (' + e + ')'); }
  const num = s => s ? parseInt(String(s).replace(/[^\d]/g, '')) || null : null;
  for (const q of ['ガンプラ', 'ガンダム プラモデル']) {
    for (let pg = 1; pg <= 25; pg++) {
      let html;
      try { html = await fetch(`/s?k=${encodeURIComponent(q)}&i=hobby&rh=p_6%3AAN1VRQENFRJN5&page=${pg}`, { credentials: 'include' }).then(r => r.text()); }
      catch (e) { window.__gpLog.push('err ' + q + pg); continue; }
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const els = [...doc.querySelectorAll('[data-component-type="s-search-result"]')];
      if (!els.length) break;
      window.__gpProgress = `search ${q} p${pg}`;
      for (const el of els) {
        const a = el.dataset.asin; if (!a || window.__gp[a]) continue;
        window.__gp[a] = {
          t: (el.querySelector('h2')?.textContent || '').trim().replace(/^BANDAI SPIRITS\s*\(バンダイ\s?スピリッツ\)\s*/, ''),
          p: num(el.querySelector('.a-price:not(.a-text-price) .a-offscreen')?.textContent),
          lp: num(el.querySelector('.a-price.a-text-price .a-offscreen')?.textContent),
          img: (el.querySelector('img.s-image')?.getAttribute('src') || '').match(/images\/I\/([^.]+)/)?.[1] || '',
          b: num((el.textContent.match(/過去1か月で([\d,万]+)点以上購入/) || [])[1]?.replace('万', '0000')),
        };
      }
      await sleep(1500);
    }
  }
  const isKit = t => (/(HG|RG|MG|PG|EG|ENTRY GRADE|SD|BB戦士|MGSD|RE\/100|FULL MECHANICS|1\/144|1\/100|1\/60|ガンプラ)/i.test(t)
      && /ガンダム|GUNDAM|ガンプラ|ザク|シャア|ジム|ゲルググ|ドム|グフ|サザビー|ジオン|ユニコーン|バルバトス|エアリアル|GQuuuuuuX|ストライク|フリーダム|ウイング|ゼータ|ガンキャノン|ガンタンク|SDW HEROES/i.test(t))
    && !/ASSEMBLE|デカール|マーカー|ニッパー|ヤスリ|塗料|スタンド|アクションベース|カード|30MM|30MS|30MF|30MP|ウエハース|フィギュア|ROBOT魂|超合金|METAL BUILD|一番くじ|LED|オプションパーツ|ボールチェーン|キーチェーン|メガハウス|MegaHouse|食玩|チューインガム|ガム|CONVERGE|ウエハー|BOX販売|\(× ?\d+\)/i.test(t);
  const kits = Object.entries(window.__gp).filter(([a, x]) => isKit(x.t));
  // 最近まで売っていたのに検索に出なくなった商品（売り切れ）。商品ページから名前と画像だけ読む
  for (const a of (window.__gpPrev || [])) {
    if (window.__gp[a]) continue;
    window.__gpProgress = `prev ${a}`;
    try {
      const html = await fetch(`/dp/${a}`, { credentials: 'include' }).then(r => r.text());
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const t = (doc.querySelector('#productTitle')?.textContent || '').trim().replace(/^BANDAI SPIRITS\s*\(バンダイ\s?スピリッツ\)\s*/, '');
      const img = (doc.querySelector('#landingImage')?.getAttribute('src') || '').match(/images\/I\/([^.]+)/)?.[1] || '';
      if (t) kits.push([a, { t, img, p: null, lp: null, b: null }]);
    } catch (e) { window.__gpLog.push('err prev ' + a); }
    await sleep(1300);
  }
  const out = [];
  for (const [i, [a, x]] of kits.entries()) {
    window.__gpProgress = `offers ${i + 1}/${kits.length}`;
    let amz = null, others = [], left = '';
    try {
      const html = await fetch(`/gp/product/ajax/aodAjaxMain/?asin=${a}&pc=dp&isonlyrenderofferlist=false`, { credentials: 'include' }).then(r => r.text());
      const doc = new DOMParser().parseFromString(html, 'text/html');
      for (const o of doc.querySelectorAll('#aod-pinned-offer, #aod-offer')) {
        const seller = (o.querySelector('#aod-offer-soldBy a, #aod-offer-soldBy .a-col-right span') || {}).textContent || '';
        const cond = (o.querySelector('#aod-offer-heading')?.textContent || '').trim();
        const p = num(o.querySelector('.a-price-whole')?.textContent);
        if (!p || !/^新品/.test(cond)) continue;
        if (/Amazon/i.test(seller)) { amz = amz ? Math.min(amz, p) : p; left = (o.textContent.match(/残り\s*(\d+)\s*点/) || [])[1] || left; } else others.push(p);
      }
    } catch (e) { }
    others.sort((m, n) => m - n);
    const med = others.length ? others[Math.floor(others.length / 2)] : '';
    const dot = s => String(s).split('').join('.');
    out.push([dot(a), amz || '', x.lp || '', med, others.length, dot(x.img), x.b || '', left, x.t.slice(0, 80)].join('|'));
    await sleep(1300);
  }
  window.__gpOut = out;
  window.__gpProgress = 'done';
  window.__gpDone = true;
})();
'started';
