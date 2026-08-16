# WEEKLY-REVIEW.md

Weekly retrospective written by the Sunday-evening routine. Each entry summarizes the prior week's performance and proposes (does not auto-apply) up to 3 strategy edits.

---

## 2026-08-16 — Week ending 2026-08-16

### Stats
- Trades: placed=0 filled=0 rejected=0 skipped=2 blocked=0
- Hit rate: N/A (no filled buys closed this week)
- Realized PnL: $0 (0% of NAV — no positions opened or closed)
- Max intra-week drawdown: N/A (no open positions; paper mode)
- Biggest winner: N/A; biggest loser: N/A
- KILL_SWITCH events: 0 this week

### Per-bucket attribution
- Anchor: 0 trades, $0 PnL — BTC/ETH rule-based conf consistently 0.40 < 0.55 floor
- Theme: 0 trades, $0 PnL — 1 source-type all passes; ≥2 required; all themes DORMANT
- Gem: 0 trades, $0 PnL — APR (aPriori) skipped: rank=0.91 PASS but conf=0.40 FAIL; AKE skipped: pump-profile + no news citation REJECT

### Per-theme attribution
- All themes: 0 fires, 0 fills — on-chain stream (Binance 451) and regime/FedWatch streams offline; 1 source-type throughout; threshold is 2

### Themes that fired but produced no fills
- None fired. All themes DORMANT all week — structural, not signal-driven: only the news stream is reachable from cloud egress; the other streams (on-chain, regime, FedWatch) are blocked by Binance/yfinance geo-restrictions.

### Observations
- **8 consecutive 0-trade passes.** The system is functioning — gates, forecaster, gem scanner all running. The blocker is structural: Binance testnet returns 451 from the Anthropic cloud egress region, which fail-closes both on-chain signals and crypto broker connectivity. VPS deployment (`deploy/`) is the intended fix and is the highest-priority operational gap.
- **OpenAI 429 rate limit hit on Aug-07** (news stream), silencing the only working source-type for that pass. No Perplexity fallback is configured. Configuring `PERPLEXITY_API_KEY` in the cloud env would restore news coverage on OpenAI outages/throttles.
- **Promising gem candidates blocked by conf threshold, not by logic.** CYS (Cysic, ZK compute) rank=0.957 on Aug-07 and APR (aPriori, order-flow layer) rank=0.91 on Aug-14 both cleared the rank gate and had coherent narratives but hit conf=0.40 < 0.55 floor from the rule-based forecaster. The forecaster treats low-24h momentum as "flat" regardless of 7d/30d trend, systematically penalizing high-rank gems in accumulation phases.
- **Positive signal on ATOM and LINK.** ATOM conf=1.0 (+10.9%/7d) and LINK conf=0.92 (+8.4%/7d) on Aug-14 were among the strongest signals seen this cycle. Both are large_cap (research-only) rather than anchors, so they can only be traded as gems if they clear all gem gates — a structural mismatch since they are top-30 coins, not sub-$500M mcap candidates.
- **BTC ranging $63K–$65K with no ETF inflow catalyst** to push anchor confidence above threshold. Macro is risk-off/mixed; rate environment neutral per news. No anchor trades expected until BTC/ETH show directional momentum ≥ ±3% weekly.

### Proposed strategy edits (NOT applied)
1. **Add ATOM and LINK to crypto anchors** (`themes.yaml` `crypto.anchors`): Both have been the highest-confidence signals (conf ≥ 0.92) across multiple passes while BTC/ETH are flat. The current anchor list is BTC + ETH only; adding ATOM and LINK with the same conf ≥ 0.55 gate would have captured the Aug-14 ATOM signal without relaxing any risk limit.
2. **Lower gem forecast-confidence floor to 0.50 for rank ≥ 0.80 candidates**: APR (rank=0.91) and CYS (rank=0.957) cleared every gate except conf. The rule-based forecaster scores 0.40 "flat" for coins with strong 30d/7d momentum but muted 24h — a systematic gap for accumulation-phase gems. For rank ≥ 0.80 only, reduce the conf floor from 0.55 to 0.50; thesis-length and news-citation requirements remain unchanged.
3. **Configure Perplexity as news fallback in cloud env**: `PERPLEXITY_API_KEY` unset today; the Aug-07 pass had 0 active source-types due to OpenAI 429. With Perplexity as fallback, the news stream would have been live and theme detection would have continued. This is an env-var addition, not a strategy-rule change, but it is the lowest-cost fix for the recurring single-source-type constraint.

---
