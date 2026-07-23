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

## 2026-07-23 16:15 UTC — PLACED buy 5.0 LMT

- symbol: LMT
- side: buy
- qty: 5.0
- status: placed
- mode: paper
- broker: alpaca
- order_id: 6826cf2f-f8e4-4cf4-a1c8-0ff4cf90f4da
- fill_price: -
- reason: theme=defense: Lockheed Martin Q2 2026 revenue $20.063B +11% YoY, EPS $7.94, raised FY2026 guidance to $79.75-81.75B; defense sector outperforming broad market (+11% 7d vs SPY -1.8%); cited SEC 8-K Item 2.02 filed 2026-07-23 + news coverage per investors.lockheedmartin.com Q2 results

## 2026-07-23 16:15 UTC — PLACED buy 20.0 RTX

- symbol: RTX
- side: buy
- qty: 20.0
- status: placed
- mode: paper
- broker: alpaca
- order_id: a45cb38d-1a5c-4036-bc02-d7b7bf9b2f26
- fill_price: -
- reason: theme=defense: RTX Q2 2026 revenue $24.7B +14% YoY, adj EPS $1.89 +21% YoY, raised FY2026 guidance to $95-96B sales; defense sector rotation (+8.5% 7d vs SPY -1.8%); cited SEC 8-K Item 2.02 filed 2026-07-23 + news coverage per raytheon.mediaroom.com Q2 2026 results
