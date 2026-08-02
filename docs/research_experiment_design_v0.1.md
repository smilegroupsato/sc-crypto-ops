# リサーチ実験設計 v0.1

ページ作成日時：2026-08-02 10:57 JST
最終更新日時：2026-08-02 10:57 JST

## 目的

暗号資産のリサーチ・銘柄選定・売買計画を、単発の勘ではなく、複数の選定profileとして実験する。

いまの目的は「最初から当てること」ではない。複数のチューニングで候補を多めに作り、後から、どの選定基準が有効だったか、どの根拠が外れたかを検証できる状態を作る。

## 実験単位

| 層 | 役割 | 保存先 |
|---|---|---|
| Research Profile | 選定・判断基準のチューニング単位 | `docs/research_profiles_v0.1.md` |
| Candidate Batch | 同じ観測日にprofile別で拾った候補群 | `records/research/` |
| Paper Trade Plan | 実取引前に作る売買計画。原則Watch Only | `records/trade_plans/` |
| Watch Log | 1日後、3日後、7日後、14日後、30日後の推移 | `records/watch/` |
| Outcome Review | 成功率、R倍率、最大逆行、根拠の当たり外れ | `records/reviews/` |

## 基本原則

- 候補ごとに必ず `profile_id` を付ける。
- 価格だけでなく、選定時点の根拠、却下条件、反証条件を残す。
- まずは実弾よりPaper Planを多く作る。
- 実取引へ進める場合も、Paper Planで最低1回watchしてから小口にする。
- MetaMask/DEX取引は、transaction hashを証憑IDとして記録する。
- 国内取引所取引は、CSV、約定画面、価格ソースURLを証憑にする。
- Swapは会計上、支払資産の譲渡と取得資産の取得に分解して考える。
- 税務判断が不明なものは、取引実行ではなくWatchで止める。

## 検証指標

| 指標 | 内容 |
|---|---|
| Hit判定 | Plan作成後30日以内に利確1へ到達したか |
| Stop判定 | Plan作成後30日以内に損切り条件へ到達したか |
| R倍率 | `想定利益 / 想定損失`。Paperでも算出する |
| 最大順行 | Entry基準価格から最も上に行った割合 |
| 最大逆行 | Entry基準価格から最も下に行った割合 |
| 根拠の有効性 | 選定理由が価格・出来高・実需に反映されたか |
| 記帳容易性 | Google Sheetに証憑付きで記録できたか |
| 実行容易性 | 取引経路、ガス代、流動性、スリッページが許容範囲か |

## Watchタイミング

| タイミング | 見るもの |
|---|---|
| T+1日 | 急変、材料否定、出来高継続 |
| T+3日 | Entry後の初期方向、損切り接近 |
| T+7日 | 短期planの妥当性 |
| T+14日 | テーマ継続、出来高減衰 |
| T+30日 | 成功/失敗/無効の判定 |

## 判定区分

| 判定 | 内容 |
|---|---|
| Success | 利確1へ到達、またはplan通りに優位性が確認できた |
| Partial | 利確未達だが根拠は継続。損切り未到達 |
| Failed | 損切り到達、または根拠が明確に崩れた |
| Invalidated | 取引経路、規制、証憑、会計処理の問題でplan自体を無効化 |
| No Trade | Entry条件未達。検証サンプルとしては残す |

## ファイル命名

```text
records/research/YYYY.MM.DD_NN_multi_profile_candidate_batch.md
records/trade_plans/YYYY.MM.DD_NN_<symbol>_<profile_id>_paper_plan.md
records/watch/YYYY.MM.DD_NN_watch_log_<batch_id>.md
records/reviews/YYYY.MM.DD_NN_outcome_review_<batch_id>.md
```

## 更新履歴

- 2026-08-02 10:57 JST：複数profileでの銘柄選定・Paper Plan・Watch検証の実験設計を作成。
