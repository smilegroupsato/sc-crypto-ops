# On-chain Transaction証憑ルール v0.1

ページ作成日時：2026-08-02 10:57 JST
最終更新日時：2026-08-02 10:57 JST

## 目的

国内取引所に限らず、MetaMask接続で売買できる暗号資産を対象にするため、オンチェーン取引の証憑・記帳ルールを固定する。

## 対象

- MetaMaskからのSwap
- Uniswap等のDEX取引
- ERC-20 tokenのApprove
- Bridge
- Claim
- Gas feeのみ発生する失敗transaction

## 必ず残す証憑

| 証憑 | 内容 |
|---|---|
| TxHash | transaction hash。Google Sheetの `注文ID / TxHash` に入れる |
| Explorer URL | Etherscan / BaseScan / Arbiscan等のURL |
| MetaMask Activity | 取引直後の画面スクショ |
| DEX quote/receipt | Swap前の見積り、Swap後の約定情報 |
| 価格ソース | CoinGecko/CMC等の価格ページ、取得日時 |
| Gas fee | native token数量とJPY換算額 |

## 記帳原則

| 取引 | 記帳 |
|---|---|
| Approve | 原則としてガス費のみ記録。token取得/譲渡は発生しない |
| Swap | 支払資産の譲渡行と、取得資産の取得行に分解する |
| Bridge | 出金/入金/手数料を分けて記録。税務判断は要確認 |
| Failed tx | ガス費のみ記録 |
| Airdrop/Claim | 取得時価JPY、ガス費、課税判断を要確認にする |

## 証憑ID

推奨形式：

```text
EV-YYYYMMDD-ONCHAIN-001
```

## 月次確認

- Explorer上でTxHashが開けること。
- 支払資産、取得資産、数量がMetaMask/DEX/Explorerで一致すること。
- Gas feeのnative token数量を記録していること。
- 価格ソースURLとJPY換算日時が残っていること。
- `チェック` が `OK` または `要確認` に分類されていること。

## 禁止

- seed phrase、秘密鍵、private key、2FA情報をrepoやSheetに置かない。
- token contract addressを未確認のまま売買しない。
- 税務処理が不明な取引を月次締めでOKにしない。

## 更新履歴

- 2026-08-02 10:57 JST：MetaMask/DEX取引を対象にしたtransaction証憑ルールを作成。
