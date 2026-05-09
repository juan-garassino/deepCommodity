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

## 2026-05-09 22:05 UTC — BLOCKED buy 1000 JUP

- symbol: JUP
- side: buy
- qty: 1000
- status: blocked
- mode: paper
- broker: -
- order_id: -
- fill_price: -
- reason: 22:00 UTC decision: rank=0.7666 conf=1.0 7d+37.8%; ccxt not installed
