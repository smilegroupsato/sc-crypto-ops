# SC Crypto Ops

ページ作成日時：2026-08-02 08:04 JST
最終更新日時：2026-08-02 10:57 JST

SC法人の暗号資産短期売買・会計元帳・リサーチ運用を管理する private repository。

## 目的

- 売買ルールを明文化し、感情トレードを防ぐ。
- Google Sheets の暗号資産会計元帳と、Drive上の証憑原本を正本関係として運用する。
- 取引前の判断、取引後の記録、月次確認、税理士確認を同じ流れに載せる。
- JPT暗号資産会計で発生した「後からJPY価格・取引区分・証憑が追えない」問題をSCでは避ける。
- 複数のResearch Profileで銘柄選定・Paper Plan・Watch検証を行い、判断基準の成功率を測定する。

## 正本関係

| 領域 | 正本 | 役割 |
|---|---|---|
| 会計作業元帳 | [暗号資産会計元帳](https://docs.google.com/spreadsheets/d/1-CwaMmE4RBFk7lCk1KPUPlitnybQIXczeeoYy4o1p3U/edit) | 取引明細、JPY換算、保有残高、実現損益、期末評価 |
| ルール・仕様 | このrepository | 売買ルール、元帳仕様、月次チェック、運用履歴 |
| 証憑原本 | Google Drive / Dropbox | 取引所CSV、スクリーンショット、Tx控え、価格ソース控え |
| リサーチ記録 | GitHub重要記録 / Notion DB想定 | 銘柄調査、profile、Paper Plan、Watch Log、Outcome Review |
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
| 運用ステータス | v0.1 計算補助ロジック追加済、Research Routine追加済、Research Experiment開始 |

## ファイル構成

| Path | 内容 |
|---|---|
| `docs/rulebook_v0.1.md` | 売買ルール、資金枠、禁止事項 |
| `docs/ledger_schema_v0.1.md` | Google Sheets元帳のタブ・列・入力ルール |
| `docs/accounting_notes_v0.1.md` | 法人会計・税務確認メモ |
| `docs/monthly_close_checklist.md` | 月次締めチェックリスト |
| `docs/research_workflow_v0.1.md` | 銘柄調査・判断ログの運用 |
| `docs/research_routine_v0.1.md` | CoinGecko等を使った日次/候補検証ルーティン |
| `docs/research_experiment_design_v0.1.md` | 複数profileでPaper Planを作り、Watch検証する実験設計 |
| `docs/research_profiles_v0.1.md` | 銘柄選定profileの定義 |
| `docs/onchain_tx_evidence_v0.1.md` | MetaMask/DEX transaction証憑ルール |
| `templates/trade_plan_template.md` | 取引前プラン / Paper Trade Plan |
| `templates/research_note_template.md` | リサーチメモ |
| `templates/daily_research_log_template.md` | 日次リサーチログ |
| `templates/candidate_batch_template.md` | profile別候補バッチ |
| `templates/watch_log_template.md` | Watch検証ログ |
| `records/operations/` | 運用ログ置き場 |
| `records/research/` | GitHubに残す必要がある調査メモ置き場 |
| `records/trade_plans/` | Paper Plan / 取引前プラン |
| `records/watch/` | Watch Log |
| `records/reviews/` | Outcome Review |

## 絶対に置かないもの

- MetaMaskのシードフレーズ、秘密鍵
- 取引所APIキー
- 2FAバックアップコード
- ウォレット復旧情報
- 未加工の機微な証憑原本
- 個人・法人のログイン情報

## 次の一手

1. `records/research/2026.08.02_02_multi_profile_candidate_batch.md` をT+1/T+3/T+7/T+14/T+30でwatchする。
2. `templates/watch_log_template.md` を使い、各profileの最大順行・最大逆行・Success/Failed/No Tradeを記録する。
3. 実取引に進める場合は、Paper Planを再確認し、価格・ガス代・証憑・最大損失10,000円以内を更新してから実行する。
4. 税理士へ `docs/onchain_tx_evidence_v0.1.md` とGoogle Sheet元帳を共有して、MetaMask/DEX取引の記録形式を確認する。

## 更新履歴

- 2026-08-02 10:57 JST：Research Experiment、Research Profiles、On-chain Tx証憑ルール、初回multi-profile batchを追加。
- 2026-08-02 10:19 JST：Research Routineと日次リサーチログテンプレートを追加。
- 2026-08-02 08:04 JST：初期文書一式を作成。
