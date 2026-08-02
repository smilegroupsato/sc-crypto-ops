# 暗号資産リサーチ運用 v0.1

ページ作成日時：2026-08-02 08:04 JST
最終更新日時：2026-08-02 10:57 JST

## 目的

海外X、上場情報、オンチェーン情報、出来高、アンロック、価格ソースを見て、取引前判断を記録する。

Xの熱狂をそのまま売買理由にしない。Xは早期警報として扱い、価格・出来高・上場・アンロック・オンチェーンで検証する。

日次・候補検証の具体的な手順は `docs/research_routine_v0.1.md` を正本とする。

複数の選定基準を比較する実験は `docs/research_experiment_design_v0.1.md` と `docs/research_profiles_v0.1.md` を正本とする。

MetaMask/DEX取引の証憑は `docs/onchain_tx_evidence_v0.1.md` を優先する。

## リサーチ台帳の推奨フィールド

| フィールド | 内容 |
|---|---|
| profile_id | 銘柄を拾ったResearch Profile |
| batch_id | 候補バッチID |
| plan_id | Paper Plan / 取引前プランID |
| 銘柄 | トークンシンボル |
| プロジェクト名 | 正式名称 |
| チェーン | Ethereum / Solana等 |
| 情報ソース | X / 公式 / CEX / On-chain / Data |
| ソースURL | 投稿・公式発表・データURL |
| 発見日時(JST) | 最初に見つけた日時 |
| 材料 | 上場、提携、エアドロ、TVL、収益、資金流入など |
| 出来高確認 | 増加/横ばい/不明 |
| BTC/ETH環境 | 良い/中立/悪い |
| アンロック確認 | 問題なし/要注意/不明 |
| 取引判断 | Watch / Entry候補 / Paper Plan / 見送り / 終了 |
| 取引プランURL | GitHubまたはNotionの取引前プラン |
| 結果 | 勝ち/負け/未取引/見送り/検証中 |
| 反省 | 事実ベースで記録 |

## Entry候補にする条件

詳細な昇格条件と却下条件は `docs/research_routine_v0.1.md` を優先する。

| No | 条件 |
|---:|---|
| 1 | 情報ソースが1つではない |
| 2 | 公式または準公式情報で裏取りできる |
| 3 | 出来高が増えている |
| 4 | BTC/ETHが崩れていない |
| 5 | アンロックが近すぎない |
| 6 | 損切り価格と利確価格を先に書ける |
| 7 | 1回の最大損失が10,000円以内 |
| 8 | profile_id、batch_id、plan_idで後から検証できる |

## Xリスト分類

| リスト | 用途 |
|---|---|
| Breaking | 市場ニュース、速報 |
| Listings | CEX上場・取扱開始 |
| On-chain | Whale、Smart Money、資金流入 |
| Data | TVL、Fees、Unlocks、Trending |

## GitHubに残すもの

- 取引前プラン / Paper Plan
- Research Profile定義
- Candidate Batch
- Watch Log
- Outcome Review
- ルール変更
- 月次運用レビュー
- 税理士確認で決まった仕様変更
- Notion/Sheetだけでは埋もれそうな重要判断
- 日次リサーチログのうち、後で売買判断や運用改善に効くもの

## 更新履歴

- 2026-08-02 10:57 JST：Research Experiment、profile_id、batch_id、plan_id、On-chain証憑ルールへの接続を追加。
- 2026-08-02 10:19 JST：Research Routine文書への接続を追加。
- 2026-08-02 08:04 JST：初期版を作成。
