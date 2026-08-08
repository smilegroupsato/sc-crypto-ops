# Portfolio Stateful Paper v0.1

ページ作成日時：2026-08-08 15:05 JST
最終更新日時：2026-08-08 15:05 JST

## 目的

暗号資産プロジェクト全体で、`portfolio` を設定・状態管理の基本単位にする。

GatewayはIntentを直接実行するのではなく、必ず `portfolio_id` を起点に、portfolio configを読み、portfolio stateを更新する。Intent側からportfolioの安全設定、実行モード、承認ポリシー、risk limitsを緩めることはできない。

## 正本ファイル

| Path | 役割 |
|---|---|
| `gateway-adapter/config/portfolios.v0.1.json` | portfolioごとの資金配分、entry matrix profile、実行モード、承認ポリシー、risk limits |
| `gateway-adapter/state/portfolio-state.v0.1.json` | portfolioごとのcash、保有数量、平均Entry、評価額、損益、実行済Intent |
| `gateway-adapter/intent-schema-v0.1.json` | `portfolio_id` と `idempotency_key` を必須にしたIntent Schema |
| `gateway-adapter/tool/portfolio_engine.py` | Stateful Paper ExecutorとDashboard Projector |
| `dashboard/crypto-pdca/data.json` | GitHub Pages用投影データ。Portfolio Stateから生成する |

## 初期portfolio

| portfolio_id | 内容 | 初期設定 |
|---|---|---|
| `core45_cash55` | Core 45 / Cash 55 paper実験 | cash 55%、investment 45%、paper、approval_policy=`auto` |
| `speculative_meme_parallel` | Speculative / Meme Parallel paper実験 | cash 55%、investment 45%、paper、approval_policy=`auto` |

## Intentの追加必須項目

| Field | 内容 |
|---|---|
| `portfolio_id` | 実行対象portfolio |
| `idempotency_key` | 同じ注文を二重実行しないための安定キー |

`execution_mode` と `approval_policy` はIntentにも現れるが、portfolio configより緩い方向には変更できない。例えばportfolioが `paper` の場合、Intentが `live_confirmed` や `live_auto` を要求しても拒否する。

## Stateful Paper Executor

v0.1では `BUY` / `SELL` のpaper実行だけを扱う。

### 管理する状態

| State | 内容 |
|---|---|
| `cash_jpy` | portfolioごとのpaper現金 |
| `positions.*.quantity` | 保有数量 |
| `positions.*.average_entry_jpy` | 平均Entry価格 |
| `positions.*.current_valuation_jpy` | 現在評価額 |
| `realized_pnl_jpy` | 実現損益 |
| `positions.*.unrealized_pnl_jpy` | 未実現損益 |
| `total_asset_jpy` | cash + open position valuation |
| `executed_intents` | 実行済Intentの記録 |
| `idempotency_keys` | 二重実行防止キー |

### BUY

- `asset_flow.amount_jpy` をpaper購入額として扱う。
- `asset_flow.price_limit` が `JPY` のとき、paper約定価格として扱う。
- portfolioの `min_cash_jpy` を割る場合は拒否する。
- portfolioの `max_order_jpy` / `max_position_cost_jpy` を超える場合は拒否する。
- 手数料見込みは `fee_jpy_max` を上限にpaper現金から差し引く。

### SELL

- `amount_type=full_balance`、`from_amount`、または `amount_jpy` で売却数量を決める。
- 平均Entryに基づいて実現損益を計算する。
- 全数量を売却した場合はpositionを `Closed` にする。

## Dashboard Projector

`python3 gateway-adapter/tool/server.py --project-dashboard` を実行すると、`gateway-adapter/state/portfolio-state.v0.1.json` を読み、`dashboard/crypto-pdca/data.json` を生成する。

既存Dashboardの見た目を維持するため、次を同時に出力する。

| Key | 内容 |
|---|---|
| `portfolios` | portfolioごとの総資産、損益、損益率、保有銘柄、数量、Entry価格、現在価格、判断 |
| `positions` | 既存Dashboard互換の保有一覧 |
| `scenarioSummary` | 既存Dashboard互換のCore/Memeサマリー |
| `portfolioConfig` | 投影時に使ったportfolio config |

Scheduled Task側の投資判断ロジックはここでは扱わない。判断ロジックは今後、Portfolio Stateを入力として別レーンで実装する。

## 更新履歴

- 2026-08-08 15:05 JST：portfolio config/state、Stateful Paper Executor、Dashboard Projectorの仕様を作成。
