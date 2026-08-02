# リサーチProfile定義 v0.1

ページ作成日時：2026-08-02 10:57 JST
最終更新日時：2026-08-02 10:57 JST

## 目的

銘柄選定のチューニングをprofileとして固定し、後から成績と判断基準を比較できるようにする。

## Profile一覧

| profile_id | 狙い | 主な情報源 | 初期サンプル |
|---|---|---|---|
| `large_defi_quality_v0.1` | 大型DeFiの実需・収益・流動性を重視 | DefiLlama fees/revenue、CoinGecko、MetaMask | AAVE |
| `trending_momentum_v0.1` | 短期の話題化、出来高、可視性を重視 | CoinGecko Trending、CMC Trending/Gainers、MetaMask | UNI |
| `onchain_growth_v0.1` | TVL、fees、chain/ecosystem成長を重視 | DefiLlama protocol/chain、DEX volume | AERO |
| `narrative_rwa_v0.1` | RWA、tokenized asset、機関投資家テーマを重視 | 公式情報、CoinGecko category、MetaMask、DefiLlama | ONDO |
| `narrative_synthetic_dollar_v0.1` | synthetic dollar / stablecoin周辺テーマを重視 | DefiLlama stablecoins/protocol、CoinGecko、MetaMask | ENA |
| `domestic_easy_accounting_v0.1` | 国内取引所・証憑・JPY記帳の容易性を重視 | 国内取引所一覧、CoinGecko/CMC、DefiLlama chain | SOL |

## 共通ゲート

| ゲート | 条件 |
|---|---|
| 市況 | BTC/ETHが急落中ならEntry不可。候補記録のみ |
| 流動性 | 取引できるだけの出来高・DEX流動性がある |
| 証憑 | TxHash、ブロックエクスプローラ、取引所CSV、スクショ等を残せる |
| 損失上限 | 実取引に進める場合、1planの最大損失は10,000円以内 |
| 記録 | Google Sheetに、数量、JPY換算、手数料、ガス、証憑IDを記録できる |

## profile別の見方

### large_defi_quality_v0.1

重視するもの：

- protocol fees / revenue
- TVLまたは利用実績
- 市場規模と流動性
- MetaMaskまたは主要DEXでの取引可能性
- token value captureの説明しやすさ

却下条件：

- 実需はあるがtokenに価値が戻る説明が弱い
- 直近の重大ガバナンス/規制リスクがある
- 流動性が薄い

### trending_momentum_v0.1

重視するもの：

- CoinGecko/CMC上の可視性
- 24h出来高の増加
- 7d/30dでの初動
- SNSだけではなくデータで確認できること

却下条件：

- 急騰後の追撃だけ
- 出来高が伴わない
- 材料がXの煽りのみ

### onchain_growth_v0.1

重視するもの：

- DefiLlamaでTVL/fees/revenueが確認できる
- chain/ecosystem成長の中心にいる
- protocol利用とtoken需要の関係を説明できる

却下条件：

- 排出/emissionが強すぎる
- protocolは強いがtoken希薄化が重い
- DEX流動性やExitが弱い

### narrative_rwa_v0.1

重視するもの：

- tokenized assets / RWA / capital markets onchain
- 公式発表や統合の有無
- 規制・利用制限を確認できること

却下条件：

- KYC/地域制限により実質的に利用できない
- 規制リスクを説明できない
- token保有の意味が不明

### narrative_synthetic_dollar_v0.1

重視するもの：

- stablecoin / synthetic dollar供給量
- protocol fees / revenue
- collateral、hedging、peg riskの説明可能性

却下条件：

- 商品構造を説明できない
- revenueとtoken value captureのズレが大きい
- depeg、funding、規制リスクが大きい

### domestic_easy_accounting_v0.1

重視するもの：

- 国内取引所での法人アカウント売買可能性
- CSV、JPY約定、手数料記録の容易性
- 会計元帳への入力の簡単さ

却下条件：

- 取扱はあるが法人アカウントで売買できない
- 約定データが取りづらい
- 入出金・証憑保存が面倒すぎる

## 更新履歴

- 2026-08-02 10:57 JST：初期profile 6件を定義。
