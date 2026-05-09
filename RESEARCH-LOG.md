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

### Top 5 Ranked Opportunities (22:00 UTC, crypto-only pass)

| Rank | Symbol | Score | Price USD | Mcap USD | Momentum | Mcap Score |
|------|--------|-------|-----------|----------|----------|------------|
| 1 | JUP | 0.7666 | 0.2490 | 827M | 1.000 | 0.914 |
| 2 | TIA | 0.6383 | 0.4417 | 404M | 0.595 | 1.000 |
| 3 | NEAR | 0.5375 | 1.5600 | 2.0B | 0.534 | 0.806 |
| 4 | INJ | 0.5168 | 4.2300 | 423M | 0.297 | 0.995 |
| 5 | FET | 0.5136 | 0.2332 | 527M | 0.314 | 0.968 |

Note: JUP score 0.7666 exceeds min threshold (0.55); TIA at 0.6383 also above threshold.
NEAR/INJ/FET are borderline (0.51–0.54, below 0.55 threshold).

### Tier 1 Anchors
- BTC: $80,760 (+0.58% 24h, +2.57% 7d), mcap $1.62T
- ETH: $2,330.60 (+0.62% 24h), mcap $281B
- SOL: $93.41, mcap $54B

### News Bullets (6h digest)
- US equity ETFs saw $9.3B institutional outflow; macro risk-off signal for equities.
- Shanghai/Shenzhen cross-border ETF net outflow 789B yuan this week.
- USD index -0.4% to 97.877 on US-Iran optimism; crypto mildly bid.
- No new Fed rate decisions in window; next catalyst TBD.

### Anomalies
- Volume scores near zero across all ranked symbols (0.001–0.009); thin liquidity regime.
- Equities skipped (22:00 UTC, outside 13-21 window); crypto-only pass.
- BINANCE_API_KEY absent — data sourced via public CoinGecko endpoint (no order book depth).
