# WEEKLY-REVIEW.md

Weekly retrospective written by the Sunday-evening routine. Each entry summarizes the prior week's performance and proposes (does not auto-apply) up to 3 strategy edits.

---

## 2026-08-02 — Week ending 2026-08-02

### Stats
- Trades: placed=0 filled=0 rejected=0 skipped=0 blocked=1 (risk_check level; never reached place_order)
- Hit rate: N/A (0 closed trades)
- Realized PnL: $0 (0.0% of starting NAV)
- Max intra-week drawdown: unavailable (Binance testnet NAV unreachable each check_drawdown run)
- Biggest winner: none; biggest loser: none
- KILL_SWITCH events: 0

### Per-bucket attribution
- Anchor: 0 trades, $0 — BTC/ETH rule-based conf 0.40 consistently below 0.55 gate
- Theme:  0 trades, $0 — only 1 source-type (news) reachable; all themes dormant
- Gem:    0 fills, $0 — BTW (Bitway, +27.7%/7d, rank 0.671, conf 1.0) passed all gates 2026-07-31 but risk_check BLOCKED (Binance testnet 451 geo-block from cloud)

### Per-theme attribution
- All themes: 0 trades — structural gap, not signal failure. On-chain, cross-asset regime, and FedWatch all failing from Anthropic cloud egress; never reached ≥2 distinct source-types.

### Themes that fired but produced no fills
- **crypto_proxy** — BTC ETF $797M/24h inflows (2026-07-24), $9B 4-month trend (2026-07-31); signal present in news but only 1 source-type confirmed; dormant by rule.

### Observations
- **Zero execution, structural not signal.** The trading system is functioning correctly — gates are passing candidates (BTW gem 2026-07-31, KAITO gem 2026-07-17) but Binance testnet is geo-blocked (HTTP 451) from Anthropic cloud egress every run. The VPS deployment in `europe-west1-b` resolves this; cloud routines cannot trade crypto until then.
- **Rule-based forecaster anchored at 0.40 for BTC/ETH.** Both assets scored flat 0.40 across all four decision passes this month despite BTC ETF inflows ranging $253M–$797M/day. The rule-based model uses 7d/24h momentum ratio; sideways 7d price action (BTC +1.7%/7d to -0.6%/7d) correctly produces "flat", but strong institutional inflow is not captured. ETF flow data is a potential signal improvement.
- **rank_smallcaps format mismatch blocking gem lane.** Multiple passes report "rank_smallcaps returned empty (format mismatch)." This means gem scoring cannot be validated — the lane is structurally blocked regardless of broker availability. Needs a targeted debug of the output schema expected by `tools/rank_smallcaps.py`.
- **Promising gem pipeline.** KAITO (AI InfoFi, +131%/30d, $205M mcap, July 17), UB/Unibase (+58.7%/7d, AI memory, July 24), BTW/Bitway (+27.7%/7d, +59.6%/30d, July 31) are all credible gem candidates. Once VPS and rank_smallcaps are operational, this lane should produce fills.
- **One open position: AAPL (paper, smoke-test).** 1 AAPL share from 2026-05-09 smoke test, entry price not recorded — stop/TP uncomputable. Position-mgmt is correctly holding and deferring to manual review. Consider logging a synthetic $310.69 entry price (2026-05-09 close) to enable automated stop/TP tracking.

### Proposed strategy edits (NOT applied)
1. **Fix rank_smallcaps format mismatch.** Add an integration test or schema validation in `tools/rank_smallcaps.py` that confirms JSON output shape matches what decision routine expects. The gem lane has been structurally blocked for ≥4 consecutive passes.
2. **Augment rule-based forecaster with ETF-flow signal.** Add a `flow_signal` input to `tools/forecast.py --model rule-based`: if `news_digest` contains BTC/ETH ETF inflow > $500M/day, boost confidence by +0.15 (capped at 0.85). This would have cleared the anchor gate on 2026-07-17 ($753M) and 2026-07-24 ($797M).
3. **Record smoke-test trades with fill_price.** Update `tools/place_order.py` or the smoke script to always record a synthetic fill price (midpoint of bid/ask or last trade) for paper orders. Without it, stop/TP logic is uncomputable and position-mgmt cannot manage the position.
