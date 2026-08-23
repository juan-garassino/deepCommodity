# WEEKLY-REVIEW.md

Weekly retrospective written by the Sunday-evening routine. Each entry summarizes the prior week's performance and proposes (does not auto-apply) up to 3 strategy edits.

---

## 2026-08-23 — Week ending 2026-08-23

### Stats
- Trades: placed=0 filled=0 rejected=0 skipped=0 blocked=0
- Hit rate: N/A (no filled buys closed this week)
- Realized PnL: $0 (0% of NAV — no positions opened or closed)
- Max intra-week drawdown: N/A (no open positions with known NAV; Binance testnet geo-blocked)
- Biggest winner: N/A; biggest loser: N/A
- KILL_SWITCH events: 0 this week

### Per-bucket attribution
- Anchor: 0 trades, $0 PnL — BTC conf=0.40 / ETH conf=0.40, both <0.55 floor; 24h flat overrides 7d momentum in rule-based forecaster
- Theme: 0 trades, $0 PnL — all themes DORMANT; 1 source-type (news only) throughout week; ≥2 required
- Gem: 0 trades, $0 PnL — CAP rank=0.717 PASS but no news thesis citation → blocked; AKE rank=0.591 FAIL

### Per-theme attribution
- All themes: 0 fires, 0 fills — structural: on-chain (Binance 451), regime (yfinance unreachable), FedWatch (yfinance unreachable) streams all offline from cloud egress; only news stream active

### Themes that fired but produced no fills
- None fired. All themes DORMANT all week — 1 active source-type (news) < 2 required. Structural cloud egress constraint, not signal weakness.

### Observations
- **10 consecutive cloud 0-trade decision passes.** The system is functioning — gates, forecaster, gem scanner all operating. Root cause unchanged: Binance testnet returns HTTP 451 from Anthropic cloud egress, fail-closing on-chain signals and crypto broker connectivity. VPS deployment remains the critical gap.
- **LINK hit conf=1.000 on Aug-19 (+11.1%/7d).** Strongest signal seen in this cycle — now two consecutive weeks at the top of the universe. As a top-30 coin it cannot enter via the gem lane (>$500M mcap) and is not on the anchor list. The signal is real but structurally unroutable from cloud routines.
- **BTC ETF weekly inflows at 4-month high concurrent with a 3-day outflow streak.** The rule-based forecaster scored BTC flat (0.40) based on 24h change (0.0%), missing the structural ETF flow divergence that the news stream captured. Institutional accumulation signal not reaching the confidence calculation.
- **CAP (DeFi credit, rank=0.717)** cleared the gem rank gate for the first time but was blocked at the thesis gate — no news had been fetched for CAP before rank evaluation, so no citation was available. The gem lane fetches news only after ranking, meaning high-rank candidates with no prior news context will systematically fail the thesis requirement.
- **AAPL smoke-test position (paper, May 2026)** persists as only open position with no entry price recorded, making stop/TP thresholds uncomputable. Position-mgmt correctly held but cannot manage risk on this artifact position.

### Proposed strategy edits (NOT applied)
1. **Add LINK to crypto anchor list** (`TRADING-STRATEGY.md` and `themes.yaml` `crypto.anchors`): LINK conf=1.000 on both Aug-14 and Aug-19, the highest signals in the universe two weeks running. Top-30 by market cap, liquid, and showing consistent directional momentum that the current anchor list (BTC + ETH only) cannot trade. Same conf ≥ 0.55 gate applies — no risk parameter change needed.
2. **Prefetch news for top-3 gem candidates before thesis evaluation**: The current gem lane runs `scan_hidden_gems → rank_smallcaps → thesis write` where news is fetched only to write the thesis. CAP (rank=0.717) and similar candidates are blocked because the agent has no news context at thesis time. Running `fetch_news.py --query "<gem_name> crypto"` for the top-3 ranked gems before thesis construction would eliminate "rank PASS, no thesis citation" blocks at low marginal OpenAI cost (~3 × $0.04).
3. **Multi-window anchor confidence: `max(24h_signal, 7d_signal)` for BTC/ETH**: The rule-based forecaster uses 24h return only, scoring BTC as "flat" (0.40) when 24h=0.0% even as 7d=+1.0% and ETF weekly inflows are at a 4-month high. For anchor symbols only, treating the confidence as `max(conf_24h, conf_7d)` would have scored BTC above threshold on Aug-19 — a minimal change to the forecasting logic that better captures the medium-term momentum anchors are selected for.

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
