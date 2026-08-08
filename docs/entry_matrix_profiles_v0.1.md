# Entry Matrix Profiles v0.1

ページ作成日時：2026-08-08 16:51 JST
最終更新日時：2026-08-08 16:51 JST

## 目的

`core45_cash55` と `speculative_meme_parallel` の投資判断を portfolio-aware 化するため、現行 Entry Matrix を baseline として保存し、Portfolio 別の Entry Matrix profile を定義する。

この文書は投資判断側の評価基準を定義する。Portfolio 残高、数量、約定、実現/未実現損益の正本は Gateway とし、投資運用チャット、Dashboard、日次PDCAログは独自の Portfolio State を持たない。

## 適用範囲

| 項目 | 方針 |
|---|---|
| 対象Portfolio | `core45_cash55` / `speculative_meme_parallel` |
| 対応config | `gateway-adapter/config/portfolios.v0.1.json` |
| Portfolio State正本 | `gateway-adapter/state/portfolio-state.v0.1.json` |
| 表示用投影 | `dashboard/crypto-pdca/data.json` |
| 現行Matrix | `baseline_v0` として保存 |
| 今回変更しないもの | `portfolios.v0.1.json`、Gateway State、standalone scheduled task |

## 参照した根拠

| 種別 | 参照元 | 要点 |
|---|---|---|
| 現行Matrix | `records/pdca/2026.08.04_04_entry_matrix_prediction_improvement.md` | 12項目100点満点の単一baseline。Meme実践データ2本から作成 |
| 日次PDCA | `records/pdca/2026.08.07_02_daily_crypto_pdca_simulation.md` | PUMP強、USELESS弱、PLUME/SKYAI/CYS Watch、追撃抑制 |
| 日次PDCA | `records/pdca/2026.08.08_01_daily_crypto_pdca_simulation.md` | Coreは+0.26%、Memeは-0.85%。BONK Stop、PEPE Add、USELESS Stop近接 |
| Gateway config | `gateway-adapter/config/portfolios.v0.1.json` | profile名、risk_limits、allowed_assets、paper/auto方針 |
| Dashboard投影 | `dashboard/crypto-pdca/data.json` | Portfolio別ポジション、損益、判断、Entry Matrix表示用データ |

## baseline_v0

現行Matrixを `baseline_v0` として残す。これは主に Speculative / Meme Parallel の初期運用から作られた単一Matrixであり、CoreとMemeを分離する前の比較基準として扱う。

| 評価項目 | 重み | 見るもの |
|---|---:|---|
| 市場ゲート | 8 | BTC/ETH/SOL、カテゴリ地合い、リスクオン/オフ |
| 流動性/出口 | 12 | 24h出来高、板、取引所、Exit可能性 |
| 出来高加速 | 8 | 出来高の増減、注目の流入 |
| 価格モメンタム | 10 | 24h/7d値動き、上昇継続性 |
| 相対強度 | 8 | 同カテゴリ内での強さ |
| 材料/物語 | 10 | なぜ今買われるか、材料の持続性 |
| 上場/取引所品質 | 8 | CEX/DEX品質、出口の深さ |
| 供給/集中リスク | 8 | 保有集中、解除、FDV、インサイダー懸念。高得点ほど安全 |
| Entry位置 | 8 | 天井掴み回避、Stopを置ける位置か |
| 損益設計 | 8 | Stop幅と利確余地の比率 |
| 執行適合 | 6 | サイズ、スプレッド、税務記録、運用負荷 |
| PDCA証拠適合 | 6 | 過去ログで当たりやすかった条件との一致 |
| **合計** | **100** |  |

## Profile一覧

| Portfolio ID | Matrix Profile | 性格 | 主な目的 |
|---|---|---|---|
| `core45_cash55` | `core_45_cash_55` | Core / Cash reserve 55% | 崩れにくい中核銘柄を45%枠で保有・検証する |
| `speculative_meme_parallel` | `speculative_meme_parallel` | Speculative / Meme | 短期高ベータ候補を小さく試し、StopとFalse Negativeを検証する |

## Profile別の評価項目と重み

| 評価項目 | baseline_v0 | core_45_cash_55 | speculative_meme_parallel |
|---|---:|---:|---:|
| 市場ゲート | 8 | 10 | 7 |
| 流動性/出口 | 12 | 14 | 13 |
| 出来高加速 | 8 | 6 | 11 |
| 価格モメンタム | 10 | 6 | 11 |
| 相対強度 | 8 | 8 | 7 |
| 材料/物語 | 10 | 10 | 9 |
| 上場/取引所品質 | 8 | 12 | 6 |
| 供給/集中リスク | 8 | 12 | 9 |
| Entry位置 | 8 | 8 | 9 |
| 損益設計 | 8 | 8 | 7 |
| 執行適合 | 6 | 4 | 5 |
| PDCA証拠適合 | 6 | 2 | 6 |
| **合計** | **100** | **100** | **100** |

## CoreとMemeで分ける評価軸

| 評価軸 | Coreで重く見る | Memeで重く見る |
|---|---|---|
| 時間軸 | T+7以降も崩れにくい構造テーマ | T+1/T+3の加速と失速 |
| 流動性 | 大口でも逃げられる継続流動性 | 急変時にもExitできる短期出来高 |
| 価格 | 押し目・相対安定・下げ止まり | ブレイク・出来高加速・短期相対強度 |
| 材料 | RWA、DeFi、AI、L1/L2など継続テーマ | SNS波及、カテゴリ内連鎖、短期物語 |
| リスク | 供給解除、上場品質、プロトコル継続性 | 集中保有、材料事故、出来高枯れ、天井掴み |
| PDCA | 週次以上で重みを見直す | T+1/T+3/T+7でFalse Positive/False Negativeを早く拾う |

## Entry閾値

| Profile | BUY | ADD | HOLD | REDUCE | EXIT |
|---|---:|---:|---:|---:|---:|
| `core_45_cash_55` | 78以上 | 82以上 | 60以上 | 45〜59、またはEntry比-8%超 | Entry比-12%目安、またはthesis invalid |
| `speculative_meme_parallel` | 75以上 | 80以上 | 58以上 | 40〜57、またはEntry比-10%超 | Entry比-15〜20%、流動性低下、材料事故 |

閾値はGatewayの `risk_limits` を緩めない。MatrixがBUY/ADDでも、Portfolio config、Intent側manual要求、approval_policy、daily_order_limit_jpy、max_position_cost_jpy、max_total_investment_jpy、min_cash_jpyを満たさない場合は実行しない。

## BUY / HOLD / ADD / REDUCE / EXIT判断基準

### core_45_cash_55

| 判断 | 基準 |
|---|---|
| BUY | Score 78以上。市場ゲート、流動性/出口、上場品質、供給/集中リスクが大きく崩れていない。Entry位置が極端な追撃でない |
| HOLD | Score 60以上。短期下落があっても、構造テーマ、流動性、Exit、供給リスクが壊れていない |
| ADD | Score 82以上。既存ポジションが含み益または thesis が強化され、Gateway risk limit内。下落ナンピン目的だけのADDは禁止 |
| REDUCE | Score 45〜59、Entry比-8%超、または7dで同カテゴリに明確に劣後。ONDO型のReduce Watchを想定 |
| EXIT | Entry比-12%目安、原仮説崩壊、流動性急減、重大材料事故、またはGateway上のStop条件到達 |

### speculative_meme_parallel

| 判断 | 基準 |
|---|---|
| BUY | Score 75以上。出来高加速、短期モメンタム、出口流動性、Entry位置、損益設計が揃う。分割Entry前提 |
| HOLD | Score 58以上。利確未達、Stop未達、出来高と物語が維持。PUMP/PENGU型を想定 |
| ADD | Score 80以上。既存勝ちまたは高流動性で、max_position_cost_jpy内。PEPE型の上限内追加のみ |
| REDUCE | Score 40〜57、Entry比-10%超、出来高条件未達、集中/材料リスク上昇。ANSEM/USELESS型を想定 |
| EXIT | Entry比-15〜20%、Stop条件到達、材料事故、出来高/物語の劣化、出口不安。BONK型のPaper Stopを想定 |

## 過去データに基づく検証仮説

| 仮説 | 根拠 | 次に見るもの |
|---|---|---|
| Coreは上場品質・供給リスク・流動性を重くした方がよい | Coreは2026-08-08時点で総資産+0.26%。ONDOのみ-10%前後でReduce Watch | ONDOがStopまで行くか、AERO/ENAが相対優位を維持するか |
| Memeは出来高加速と価格モメンタムを重くする必要がある | SKYAI/CYSはWatch/見送り後にT+1急伸し、False Negative候補になった | 過熱回避で逃した上昇と、最大逆行/Stop回避の差し引き |
| Memeの小型銘柄は流動性不足と材料劣化で早く縮小すべき | USELESSは-18.47%でStop近接、ANSEMは出来高不足でReduce Watch | 出来高閾値を上げると損失が減るか |
| 高流動性MemeはADD候補になり得る | PEPEはMatrix 76.8、出来高100M USD超で10,000 JPY Paper Add | ADD後のT+1/T+3/T+7損益と最大逆行 |
| BONK型の材料事故はMatrix上で早期反映すべき | BONKはDAO treasury流出注意後、Entry比-12.88%でPaper Stop | 材料/物語、供給/集中リスク、PDCA証拠適合の減点幅 |

## 実装・運用ルール

- この文書はprofile設計の正本とする。
- `portfolios.v0.1.json` は今回変更しない。既存の `entry_matrix_profile` 名との対応だけ明記する。
- 投資運用チャットは、Gateway Stateを読んで判断し、独自の残高・数量・損益を保持しない。
- Dashboardの `data.json` は表示用投影であり、Portfolio Stateの正本ではない。
- standalone scheduled taskは今回変更しない。
- 重みは日次で動かさない。T+7または週次Outcome Reviewで、過去データまたは明示した検証仮説に基づいて見直す。

## 更新履歴

- 2026-08-08 16:51 JST：現行Matrixを `baseline_v0` として保存し、`core_45_cash_55` と `speculative_meme_parallel` の評価項目、重み、Entry閾値、BUY/HOLD/ADD/REDUCE/EXIT基準、Gateway正本ルールを追加。
