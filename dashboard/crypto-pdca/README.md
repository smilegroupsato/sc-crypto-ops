# SC Crypto Dashboard

ページ作成日時：2026-08-04 18:44 JST
最終更新日時：2026-08-04 18:44 JST

ローカルで見るための暗号資産 Paper / Watch ダッシュボードです。

## 起動

```bash
cd /srv/sgos/repos/sc-crypto-ops/dashboard/crypto-pdca
python3 -m http.server 8787 --bind 0.0.0.0
```

devbox内のブラウザなら `http://localhost:8787/`、別PCから見る場合は `http://<devboxのTailscaleまたはLAN IP>:8787/` を開きます。

## GitHub / FTP 配布

このディレクトリは静的ファイルだけで動きます。GitHub ActionsなどでFTP配布する場合は、この `dashboard/crypto-pdca/` 以下を配布対象にします。

devbox側にFTPで配置したあと、devboxのHTTPサーバから同じディレクトリを公開すれば表示できます。

## 前提

- 総資金: 1,000,000円
- Core 45 / Cash 55: 現金550,000円、投資450,000円
- Speculative / Meme Parallel: 現金550,000円、戦術現金100,000円、Meme投資350,000円
- 価格取得: CoinGecko API
- 取得失敗時: ローカルフォールバック値で表示

Meme BasketのEntry価格は、`records/pdca/2026.08.04_02_speculative_meme_parallel_entry_log.md` のT+0価格を初期値として固定しています。`Meme Entry固定` ボタンは、画面を見ながら別の時点をローカル保存したい場合だけ使います。

## 更新履歴

- 2026-08-04 18:44 JST：GitHub / FTP 配布とdevbox起動を前提にREADMEを更新。Meme Entry価格の正本ログ参照を明記。
