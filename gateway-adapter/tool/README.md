# Gateway Adapter Web Tool v0.1

ページ作成日時：2026-08-05 12:02 JST
最終更新日時：2026-08-08 15:05 JST

## 目的

スマホやブラウザから `gateway-adapter` のpaper取引adapterを操作するための最小Web UI。

これは汎用Shell Consoleではない。devbox上の任意コマンドを実行する道具ではなく、SC暗号資産GatewayのIntent検証とpaper実行だけに用途を限定する。

v0.2では、暗号資産プロジェクト全体の基本単位を `portfolio` にする。Web ToolはIntentの `portfolio_id` を読み、`gateway-adapter/config/portfolios.v0.1.json` の設定を上位正本としてRisk判定とpaper実行を行う。

## できること

| 操作 | 内容 |
|---|---|
| Intent入力 | ChatGPTやPaper Planが作ったIntent JSONを貼り付ける |
| Validate | `gateway-adapter/intent-schema-v0.1.json` とHard Guardに沿って検査する |
| Run Paper | 実発注せず、paper adapterとしてExecution Reportを作る |
| Report保存 | `gateway-adapter/records/paper-executions/` にJSONを保存する |
| Stateful Paper | portfolioごとにcash、保有数量、平均Entry、実現/未実現損益、実行済Intentを更新する |
| Dashboard Project | `gateway-adapter/state/portfolio-state.v0.1.json` から `dashboard/crypto-pdca/data.json` を生成する |

## できないこと

- 実発注
- 送金
- MetaMask署名
- 取引所API呼び出し
- DeFi/DApp実行
- seed phrase、秘密鍵、API Secret、2FA情報の入力・保存
- devbox上の任意Shell実行

## 起動

自己診断。

```bash
cd /srv/sgos/repos/sc-crypto-ops
python3 gateway-adapter/tool/server.py --self-test
```

Portfolio Stateからdashboard dataを生成する。

```bash
cd /srv/sgos/repos/sc-crypto-ops
python3 gateway-adapter/tool/server.py --project-dashboard
```

ローカルだけで試す場合。

```bash
cd /srv/sgos/repos/sc-crypto-ops
python3 gateway-adapter/tool/server.py
```

Tailscale/VPN/LAN内のスマホから開く場合。

```bash
cd /srv/sgos/repos/sc-crypto-ops
GATEWAY_UI_TOKEN='長めのランダム文字列' \
python3 gateway-adapter/tool/server.py --host 0.0.0.0 --port 8765
```

ブラウザで開く。

```text
http://devboxのTailscaleまたはLAN IP:8765/?token=長めのランダム文字列
```

## v0.1の安全制約

| 項目 | 方針 |
|---|---|
| 公開範囲 | 原則Tailscale/VPN/LAN内 |
| 認証 | 外部bind時は `GATEWAY_UI_TOKEN` または `--token` 必須 |
| 実行範囲 | `execution_mode=paper` のみ |
| Portfolio設定 | Intentではなく `gateway-adapter/config/portfolios.v0.1.json` を上位正本にする |
| 二重実行防止 | `idempotency_key` をportfolio stateに記録し、同じkeyは再実行しない |
| Hard Guard | `true` 固定。offのIntentは拒否 |
| 記録 | paper Execution ReportをJSON保存 |

## Portfolio関連ファイル

| Path | 内容 |
|---|---|
| `gateway-adapter/config/portfolios.v0.1.json` | portfolioごとの資金比率、entry matrix profile、実行モード、承認ポリシー、risk limits |
| `gateway-adapter/state/portfolio-state.v0.1.json` | portfolioごとのcash、保有数量、平均Entry、評価額、損益、実行済Intent |
| `gateway-adapter/tool/portfolio_engine.py` | Stateful Paper ExecutorとDashboard Projector |

## 更新履歴

- 2026-08-08 15:05 JST：portfolio config/state、Stateful Paper Executor、Dashboard Projectorの説明を追加。
- 2026-08-05 12:02 JST：最小Web UIの説明を作成。
