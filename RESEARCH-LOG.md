# RESEARCH-LOG.md

Append-only research notes. Written by `tools/journal.py research`. Do not edit prior entries.

---

## 2026-05-09 10:50 UTC — smoke test

- system online\n- tools layer initialized\n- this entry verifies journal.py append

## 2026-05-09 10:54 UTC — heartbeat

alive at 2026-05-09T10:54:26Z; guardrails OK; rank+forecast OK

## 2026-05-09 15:24 UTC — heartbeat

make dc-s06-heartbeat: guardrails OK, rank+forecast OK

## 2026-05-09 21:49 UTC — hourly snapshot

**Timestamp:** 2026-05-09 21:48 UTC | Crypto-only (equities skipped: alpaca-py missing)

### Top 5 Ranked (rank_smallcaps score)

| # | Symbol | Score | Price USD | 24h% | 7d% | Mcap USD |
|---|--------|-------|-----------|------|-----|----------|
| 1 | JUP    | 0.7668 | 0.2488  | +1.31 | +38.41 | 827M |
| 2 | TIA    | 0.6338 | 0.4435  | -1.72 | +22.74 | 406M |
| 3 | NEAR   | 0.5361 | 1.56    | -1.79 | +20.71 | 2.0B |
| 4 | INJ    | 0.5065 | 4.23    | -0.91 | +10.98 | 423M |
| 5 | FET    | 0.5058 | 0.2331  | -0.95 | +11.85 | 527M |

### Anchor Levels

- BTC: $80,740 (+0.69% 24h, +2.92% 7d) | intraday range $80,126–$81,026 (low vol)
- ETH: $2,329.11 (+0.76% 24h, +0.80% 7d)
- SOL: $93.40 (+1.17% 24h, +10.93% 7d)

### News Bullets

- Fed unchanged since Dec 2025 cut; IORB at 3.65% — no near-term rate catalyst
- SOL + LINK spot ETF inflows rebounded Apr 16 (SOL: $15.5M single day, largest since Mar 17) — macro-level institutional interest
- BTC holding $80K support on low intraday range — no panic selling signal

### Anomalies / Flags

- JUP 7d +38.4%: outlier momentum vs. peers; mcap score 0.914 (Tier 3 target) — warrants forecast check before any decision
- TIA 7d +22.7% + lowest mcap in set (406M) — highest mcap score but below-threshold 24h reversal
- NEAR 7d +20.7% but 24h -1.79% — short-term pullback inside a strong weekly move
- LINK 7d +13.4%: ETF inflow news provides fundamental backing; not in Tier 3, lower ranker priority
- Equities feed offline this run: alpaca-py not installed in sandbox — no equity signals
