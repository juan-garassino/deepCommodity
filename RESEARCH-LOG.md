# RESEARCH-LOG.md

Append-only research notes. Written by `tools/journal.py research`. Do not edit prior entries.

---

## 2026-05-09 10:50 UTC — smoke test

- system online\n- tools layer initialized\n- this entry verifies journal.py append

## 2026-05-09 10:54 UTC — heartbeat

alive at 2026-05-09T10:54:26Z; guardrails OK; rank+forecast OK

## 2026-05-09 15:24 UTC — heartbeat

make dc-s06-heartbeat: guardrails OK, rank+forecast OK

## 2026-05-09 21:50 UTC — daily-decision 2026-05-09

## Summary
- Date: 2026-05-09 ~21:50 UTC
- Mode: paper
- Universe: crypto-only (equities skipped: alpaca-py not installed)
- News: S&P 500 record high 7,398.93 (+0.8%), Nasdaq record 26,247 (+1.7%); crypto market positive

## Rankings (top 8 crypto, threshold ≥0.55)
- JUP:  score=0.767 ✓ momentum=1.0, mcap=0.914
- TIA:  score=0.634 ✓ momentum=0.583, mcap=1.0
- NEAR: score=0.536 ✗ (below 0.55 threshold)
- INJ:  score=0.507 ✗
- FET:  score=0.506 ✗

## Forecasts (threshold conf≥0.60)
- JUP:  long, conf=1.000 ✓ → CANDIDATE
- TIA:  flat, conf=0.400 ✗ → skipped (conf below threshold)
- SOL:  long, conf=1.000 — but rank=N/A (not in top-8 candidates; large cap)
- BTC:  long, conf=0.646 — but rank=N/A

## Decision
- JUP: rank=0.767 ✓, conf=1.000 ✓ → risk_check EXIT 0 ✓ → place_order FAILED (ccxt not installed)
- 0 orders placed, 1 skipped (broker dependency missing)

## Action needed
- pip install ccxt to enable Binance paper trading
- pip install alpaca-py to enable equity paper trading
