# RESEARCH-LOG.md

Append-only research notes. Written by `tools/journal.py research`. Do not edit prior entries.

---

## 2026-05-09 10:50 UTC — smoke test

- system online\n- tools layer initialized\n- this entry verifies journal.py append

## 2026-05-09 10:54 UTC — heartbeat

alive at 2026-05-09T10:54:26Z; guardrails OK; rank+forecast OK

## 2026-05-09 15:24 UTC — heartbeat

make dc-s06-heartbeat: guardrails OK, rank+forecast OK

## 2026-05-09 22:11 UTC — daily-decision 2026-05-09

## Context
- Mode: paper | KILL_SWITCH: absent | equities fetch: FAILED (alpaca-py missing)
- Crypto data fetched for 12 symbols; news digest retrieved via openai provider

## News highlights
- S&P 500 and Nasdaq at all-time highs; semis (NVDA, Micron) surged on AI demand
- BTC holding near \$80,730 (+0.47% 24h); ETF momentum slowing; next target \$90K uncertain
- Western Union launched USDPT stablecoin on Solana — positive for SOL ecosystem
- Dollar weakening; strong jobs data; institutional outflows of \$11B from US equities

## Rank results (top 8 crypto)
- JUP: 0.7665, TIA: 0.6393, NEAR: 0.5367, INJ: 0.5159, FET: 0.5135, RNDR: 0.4958, LINK: 0.3973, ATOM: 0.3796

## Forecast results (rule-based)
- SOL: long, confidence=1.00 (24h=+0.89%, 7d=+10.15%) — best signal today
- All other symbols: flat, confidence=0.40 (mixed short-term vs medium-term momentum)

## Gate check
- Required: rank >= 0.55 AND forecast confidence >= 0.60
- JUP/TIA pass rank but fail confidence (0.40 < 0.60)
- SOL passes confidence but not in rank top-8 (large-cap; mcap score too low)
- NO candidates cleared both gates simultaneously

## Decision
- 0 new positions placed
- 0 blocked by risk_check
- 0 orders submitted
- Note: install alpaca-py to re-enable equities universe
