# RESEARCH-LOG.md

Append-only research notes. Written by `tools/journal.py research`. Do not edit prior entries.

---

## 2026-05-09 10:50 UTC — smoke test

- system online\n- tools layer initialized\n- this entry verifies journal.py append

## 2026-05-09 10:54 UTC — heartbeat

alive at 2026-05-09T10:54:26Z; guardrails OK; rank+forecast OK

## 2026-05-09 15:24 UTC — heartbeat

make dc-s06-heartbeat: guardrails OK, rank+forecast OK

## 2026-05-09 22:08 UTC — hourly snapshot

## Top 5 Ranked Opportunities (crypto-only; equities outside market hours)

| Rank | Symbol | Score | Price USD | 7d % | MCap |
|------|--------|-------|-----------|------|------|
| 1 | JUP | 0.7666 | $0.249 | +37.84% | $827M |
| 2 | TIA | 0.6383 | $0.442 | +22.59% | $404M |
| 3 | NEAR | 0.5375 | $1.56 | +20.29% | $2.03B |
| 4 | INJ | 0.5168 | $4.23 | +11.38% | $423M |
| 5 | FET | 0.5136 | $0.233 | +12.03% | $527M |

## Anchor Prices (22:07 UTC)
- BTC: $80,760  24h=+0.58%  7d=+2.57%
- ETH: $2,331   24h=+0.64%  7d=+0.21%
- SOL: $93.41   24h=+0.94%  7d=+10.18%
- LINK: $10.41  24h=+0.29%  7d=+12.90%  (strongest tier-2 7d)

## News Bullets
- USD index -0.4% to 97.877 (US-Iran resolution optimism) — historically bullish for crypto/commodities
- $9.3B institutional outflow from US equities (institutional sell-off) — risk-off pressure on equities
- No Fed rate decision in past 6h; SPY $737.62 +0.78% (prior session)
- MRAM +25.48% (small-cap momentum outlier, not in universe)

## Anomalies
- JUP: +37.84% 7d dominates rank despite low 24h volume (vol score 0.005) — momentum-driven
- TIA: +22.59% 7d, smallest mcap in tier-3 ($404M) — highest mcap score
- NEAR: +20.29% 7d, 24h slightly negative (-0.45%) — watch for mean reversion
- Broad tier-3 rally: all 5 top-ranked assets >10% 7d return; could be overextended
- ATOM (-0.90% 24h) and FET (-1.12% 24h) weakening intraday despite strong 7d — late-rally caution
