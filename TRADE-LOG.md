# TRADE-LOG.md

Append-only trade journal. Written by `tools/journal.py trade` and by `tools/place_order.py`. Do not edit prior entries.

---

## 2026-05-09 10:51 UTC — BLOCKED buy 0.001 BTC

- symbol: BTC
- side: buy
- qty: 0.001
- status: blocked
- mode: paper
- broker: -
- order_id: -
- fill_price: -
- reason: KILL_SWITCH armed

## 2026-05-09 10:51 UTC — BLOCKED buy 0.001 BTC

- symbol: BTC
- side: buy
- qty: 0.001
- status: blocked
- mode: live
- broker: -
- order_id: -
- fill_price: -
- reason: live mode without --confirm-live

## 2026-05-09 11:02 UTC — BLOCKED buy 0.001 BTC

- symbol: BTC
- side: buy
- qty: 0.001
- status: blocked
- mode: paper
- broker: -
- order_id: -
- fill_price: -
- reason: KILL_SWITCH armed

## 2026-05-09 21:01 UTC — REJECTED buy 1.0 AAPL

- symbol: AAPL
- side: buy
- qty: 1.0
- status: rejected
- mode: paper
- broker: alpaca
- order_id: -
- fill_price: -
- reason: dc-smoke-paper end-to-end | error={"code":40110000,"message":"request is not authorized"}

## 2026-05-09 21:08 UTC — FILLED buy 1.0 AAPL

- symbol: AAPL
- side: buy
- qty: 1.0
- status: filled
- mode: paper
- broker: alpaca
- order_id: 70094dd7-3927-42c9-b277-d899c4990d7e
- fill_price: -
- reason: dc-smoke-paper end-to-end

## 2026-05-11 22:09 UTC — REJECTED buy 0.001 BTC

- symbol: BTC
- side: buy
- qty: 0.001
- status: rejected
- mode: paper
- broker: binance
- order_id: -
- fill_price: -
- reason: BTC anchor: 1,910 price with +0.86% 24h and +2.07% 7d momentum. Rule-based forecast confidence 0.604 clears anchor gate (>=0.55). No adverse regulatory or ETF flow news in 12h digest. L1/L2 ecosystem upgrade theme active (ETH Shanghai + OP Bedrock) supports broader crypto bullish backdrop. Positive sentiment; no kill-switch; paper mode. | error=binance GET https://testnet.binance.vision/api/v3/exchangeInfo
