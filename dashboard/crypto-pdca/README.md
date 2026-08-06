# SC Crypto Dashboard

ページ作成日時：2026-08-04 18:44 JST
最終更新日時：2026-08-06 18:33 JST

暗号資産 Paper / Watch ダッシュボードです。ローカル、devbox HTTPサーバ、GitHub Pages、FTP配布のどれでも静的ファイルとして表示できます。

## GitHub Pages

標準URLは次です。

```text
https://smilegroupsato.github.io/sc-crypto-ops/
```

Entry判定マトリクス専用Pageは次です。

```text
https://smilegroupsato.github.io/sc-crypto-ops/matrix.html
```

`main` に更新が入ると、`.github/workflows/deploy-crypto-dashboard-pages.yml` が `dashboard/crypto-pdca/` をPagesへデプロイします。

GitHub側で初回だけ確認する設定：

1. Repository Settings → Pages を開く。
2. Source が `GitHub Actions` になっていることを確認する。
3. Actions の `Deploy Crypto Dashboard Pages` を手動実行、または次回pushで実行する。

## ローカル起動

```bash
cd /srv/sgos/repos/sc-crypto-ops/dashboard/crypto-pdca
python3 -m http.server 8787 --bind 0.0.0.0
```

devbox内のブラウザなら `http://localhost:8787/`、別PCから見る場合は `http://<devboxのTailscaleまたはLAN IP>:8787/` を開きます。

## GitHub / FTP 配布

このディレクトリは静的ファイルだけで動きます。GitHub ActionsなどでFTP配布する場合は、この `dashboard/crypto-pdca/` 以下を配布対象にします。

devbox側にFTPで配置したあと、devboxのHTTPサーバから同じディレクトリを公開すれば表示できます。

## 日次PDCA反映

定例PDCAを回した後は、通常のMarkdownログに加えて `dashboard/crypto-pdca/data.json` も更新します。GitHub PagesはこのJSONを読み込むため、`main` に反映されると画面のポートフォリオ、推奨銘柄、新規Entry Watch、PDCA欄も最新化できます。

最低限更新する項目：

- `updatedAtJst`
- `positions`
- `fallbackPrices`
- `recommendations`
- `newEntryWatch`
- `pdca`
- `entryEvaluation`
- `predictionImprovement`

## X Account Watchlist

Xアカウントは銘柄ではなく「情報源」として扱います。投稿で出た銘柄は、そのままEntry扱いにせず、価格・出来高・流動性・市場ゲートを確認してからNew Entry WatchまたはEntry Matrixに移します。

現在の追加ログ：`records/watch/2026.08.06_01_x_account_watchlist_crypto_sources.md`

初期追加対象：

- `@crypton98`
- `@farokh`
- `@lowkeyfr`

## Entry Matrix / 予測精度改善

投機的銘柄は、`dashboard/crypto-pdca/data.json` の `entryEvaluation` を正本として評価します。

- 12項目を0から5点で採点する
- 重み付き100点満点に換算する
- 75点以上をEntry可、60点以上を小口/Watch、45点以上をWatch継続、それ未満を見送りにする
- Entry候補だけでなく、見送り候補もControl群として残す
- T+1/T+3/T+7で損益、最大逆行、出来高、相対強度、材料継続、Stop到達を検証する

詳細ログ：`records/pdca/2026.08.04_04_entry_matrix_prediction_improvement.md`

別Page：`matrix.html` は `data.json` の `entryEvaluation` を読み込み、判定帯、12項目の重み、銘柄別採点、予測精度改善ループ、検証指標を一覧表示します。

## 前提

- 総資金: 1,000,000円
- Core 45 / Cash 55: 現金550,000円、投資450,000円
- Speculative / Meme Parallel: 現金550,000円、戦術現金100,000円、Meme投資350,000円
- 価格取得: CoinGecko API
- 取得失敗時: `data.json` 内のフォールバック値で表示

Meme BasketのEntry価格は、`records/pdca/2026.08.04_02_speculative_meme_parallel_entry_log.md` のT+0価格を初期値として固定しています。`Meme Entry固定` ボタンは、画面を見ながら別の時点をローカル保存したい場合だけ使います。

## 更新履歴

- 2026-08-06 18:33 JST：X Account Watchlistの運用ルールと追加ログ参照を追記。
- 2026-08-04 21:01 JST：Entry判定マトリクス専用Page `matrix.html` を追加し、Dashboardからの導線を追加。
- 2026-08-04 20:48 JST：Entry Matrixと予測精度改善ループを追加し、data.json更新対象にentryEvaluation/predictionImprovementを追加。
- 2026-08-04 19:16 JST：画面データ正本としてdata.jsonを追加し、日次PDCA後のPages反映手順を追記。
- 2026-08-04 18:49 JST：GitHub Pagesデプロイ手順と公開URLを追記。
- 2026-08-04 18:44 JST：GitHub / FTP 配布とdevbox起動を前提にREADMEを更新。Meme Entry価格の正本ログ参照を明記。
