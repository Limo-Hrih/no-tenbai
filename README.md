# no-tenbai（NO転売ガンプラ市場）

転売価格を除いて、Amazon.co.jp本体の販売や定価に近い値段で買えるガンプラを毎日まとめる静的サイト。

## しくみ
- `src/build.py` が Amazon Creators API から「今の価格」を取得し、`dist/index.html` を生成する
- 価格・画像URLなどAmazonのデータはリポジトリに保存しない（規約で24時間までしか保存できないため）。HTMLはGitHub Actionsで毎日作り直し、Pagesに直接デプロイする
- 「今日Amazon本体で買えるようになった」判定のため、`data/state/amazon_asins.json` にASINの一覧だけを保存する
- 再販情報は `data/resale.json`（出典：バンダイ ホビーサイト「再販商品の価格改定のお知らせ」）

## 手元で試す
```
python tools/make_sample.py
python src/build.py --sample   # 見本データで生成
```

## GitHub Secrets
`CREATORS_CREDENTIAL_ID` / `CREATORS_CREDENTIAL_SECRET` / `CREATORS_CREDENTIAL_VERSION` / `PARTNER_TAG`
