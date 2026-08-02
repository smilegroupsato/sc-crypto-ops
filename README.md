# SC Crypto Ops

ページ作成日時：2026-08-02 08:04 JST
最終更新日時：2026-08-02 10:19 JST

SC法人の暗号資産短期売買・会計元帳・リサーチ運用を管理する private repository。

## 目的

- 売買ルールを明文化し、感情トレードを防ぐ。
- Google Sheets の暗号資産会計元帳と、Drive上の証憑原本を正本関係として運用する。
- 取引前の判断、取引後の記録、月次確認、税理士確認を同じ流れに載せる。
- JPT暗号資産会計で発生した「後からJPY価格・取引区分・証憑が追えない」問題をSCでは避ける。

## 正本関係

| 領域 | 正本 | 役割 |
|---|---|---|
| 会計作業元帳 | [暗号資産会計元帳](https://docs.google.com/spreadsheets/d/1-CwaMmE4RBFk7lCk1KPUPlitnybQIXczeeoYy4o1p3U/edit) | 取引明細、JPY換算、保有残高、実現損益、期末評価 |
| ルール・仕様 | このrepository | 売買ルール、元帳仕様、月次チェック、運用履歴 |
| 証憑原本 | Google Drive / Dropbox | 取引所CSV、スクリーンショット、Tx控え、価格ソース控え |
| リサーチ記録 | Notion DB想定 / GitHub重要記録 | 銘柄調査、X情報、判断ログ、ステータス管理 |
| 会計反映 | freee / 税理士資料 | 法人会計への反映、期末評価、税務判断 |

## 初期条件

| 項目 | 内容 |
|---|---|
| 取引主体 | SC法人 |
| 初期資金 | 1,000,000円 |
| 利用口座 | Coincheck / bitFlyer / 法人MetaMask |
| 基準通貨 | JPY |
| 時刻基準 | JST |
| 会計方針 | 移動平均法を前提。最終判断は税理士確認を優先 |
| 運用ステータス | v0.1 計算補助ロジック追加済、Research Routine追加済 |

## ファイル構成

| Path | 内容 |
|---|---|
| `docs/rulebook_v0.1.md` | 売買ルール、資金枠、禁止事項 |
| `docs/ledger_schema_v0.1.md` | Google Sheets元帳のタブ・列・入力ルール |
| `docs/accounting_notes_v0.1.md` | 法人会計・税務確認メモ |
| `docs/monthly_close_checklist.md` | 月次締めチェックリスト |
| `docs/research_workflow_v0.1.md` | 銘柄調査・判断ログの運用 |
| `docs/research_routine_v0.1.md` | CoinGecko等を使った日次/候補検証ルーティン |
| `templates/trade_plan_template.md` | 取引前プラン |
| `templates/research_note_template.md` | リサーチメモ |
| `templates/daily_research_log_template.md` | 日次リサーチログ |
| `records/operations/` | 運用ログ置き場 |
| `records/research/` | GitHubに残す必要がある調査メモ置き場 |

## 絶対に置かないもの

- MetaMaskのシードフレーズ、秘密鍵
- 取引所APIキー
- 2FAバックアップコード
- ウォレット復旧情報
- 未加工の機微な証憑原本
- 個人・法人のログイン情報

## 次の一手

1. `docs/research_routine_v0.1.md` に沿って、1回だけ日次15分リサーチを実施する。
2. `templates/daily_research_log_template.md` で候補なし/候補ありを記録する。
3. Entry候補が出た場合だけ、`templates/trade_plan_template.md` で取引前プランを作る。
4. 税理士へ `docs/accounting_notes_v0.1.md` とGoogle Sheet元帳を共有して、記録形式を確認する。

## 更新履歴

- 2026-08-02 10:19 JST：Research Routineと日次リサーチログテンプレートを追加。
- 2026-08-02 08:04 JST：初期文書一式を作成。
