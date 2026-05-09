# RESEARCH-LOG.md

Append-only research notes. Written by `tools/journal.py research`. Do not edit prior entries.

---

## 2026-05-09 10:50 UTC — smoke test

- system online\n- tools layer initialized\n- this entry verifies journal.py append

## 2026-05-09 10:54 UTC — heartbeat

alive at 2026-05-09T10:54:26Z; guardrails OK; rank+forecast OK

## 2026-05-09 15:24 UTC — heartbeat

make dc-s06-heartbeat: guardrails OK, rank+forecast OK

## 2026-05-09 22:05 UTC — 22:00 UTC crypto decision

Slot: 22:00 UTC, 2026-05-09, crypto-only pass.

Market context:
- BTC: +0.60% 24h, +2.58% 7d — modest upward drift
- ETH: +0.61% 24h, +0.20% 7d — flat
- News: no major regulatory or ETF events last 12h; minor price movements

Ranking (top 6, score >= 0.55):
1. JUP  0.7666 — momentum 7d +37.8%, tier-3 small-cap
2. TIA  0.6394 — momentum 7d +22.7%, tier-3 small-cap
3. NEAR 0.5363 — momentum 7d +20.2%

Forecast (confidence >= 0.60 required):
- JUP: long, conf=1.00 ✓
- TIA: flat, conf=0.40 ✗
- NEAR: flat, conf=0.40 ✗

Decision: 1 candidate passed dual gate (JUP).
Action: risk_check OK; place_order FAILED — ccxt not installed (broker dependency missing).
Trade blocked; no positions opened this slot.
