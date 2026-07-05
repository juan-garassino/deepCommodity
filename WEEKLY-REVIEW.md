# WEEKLY-REVIEW.md

Weekly retrospective written by the Sunday-evening routine. Each entry summarizes the prior week's performance and proposes (does not auto-apply) up to 3 strategy edits.

---

## 2026-07-05 — Week ending 2026-07-05

### Stats
- Trades: placed=0 filled=0 rejected=0 skipped=0 blocked=0
- Hit rate: N/A (no trades this week)
- Realized PnL: $0 (0% of NAV)
- Max intra-week drawdown: N/A (no positions open; NAV baseline unavailable)
- Biggest winner: — ; biggest loser: —

### Per-bucket attribution
- Anchor: 0 trades, $0
- Theme:  0 trades, $0
- Gem:    0 trades, $0

### Per-theme attribution
No themes produced fills this week. No decision-pass logs exist for 2026-06-29..2026-07-05 — routines did not execute.

### Themes that fired but produced no fills (within last complete decision passes — 2026-06-13)
- ai_compute (active 2x in Jun, 0 fills) — fills blocked by Binance 451 geo-block from cloud egress; broker fail-closed
- nuclear (active 1x in Jun, 0 fills) — same; equities pre-market at 12:10 UTC; prices unavailable at signal time
- defense (active 1x in Jun, 0 fills) — same broker block; LMT/RTX candidates not yet actionable before block

### Observations
- **Routine silence for 21 days (2026-06-14 → 2026-07-05).** No decision-pass or position-mgmt log entries exist in this window. Cloud routines appear to have stopped running — likely deactivated, session-expired, or scheduling disrupted. The system held zero open positions and preserved capital by default, but also missed any catalysts in this period.
- **Binance 451 geo-block remains the primary crypto execution barrier.** Every decision pass in June that identified valid crypto signals (ETH LONG 0.89, SOL LONG 0.925) hit fail-closed preflight because the Binance testnet/live endpoint returns 451 from cloud egress. VPS deployment (deploy/) is the designed fix; it has not yet been enabled as the live trading host.
- **OpenAI news provider hit 429 rate limits on at least two passes (2026-05-23, 2026-06-04).** Without news, the ≥2 distinct source-types requirement cannot be met, suppressing all theme activity. Perplexity fallback is configured but the API key is not set in the cloud env — one credential entry would halve news blackout risk.
- **KILL_SWITCH persistence gap confirmed.** On 2026-06-13, check_drawdown.py armed KILL_SWITCH, then the next run started clean (gitignored file, ephemeral container). The reliable cloud halt is DC_HALT=true in the cloud env, not the file. No halt is currently warranted; the gap is documented for operator awareness.
- **One paper fill on record (AAPL, 2026-05-09, smoke-test).** Entry price not logged — place_order returned fill_price: "-". Stop/take-profit tracking is impossible for this position. All other entries are BLOCKED or REJECTED from pre-live testing.

### Proposed strategy edits (NOT applied)
1. **Add Perplexity fallback key to cloud env** — set `PERPLEXITY_API_KEY` in the `deepCommodity` cloud environment; this is a one-credential fix that prevents full news blackouts when OpenAI hits 429, restoring the ≥2-source-types gate for theme detection.
2. **Re-enable and verify the Sunday/weekly-review routine cadence** — the 21-day silence suggests the three managed routines (`decision`, `position-mgmt`, `weekly-review`) need to be re-pasted or re-scheduled in the cloud UI; confirm all three show as active and have fired at least once before the next review.
3. **Ensure `fill_price` is recorded in place_order output** — the smoke-test fill shows `fill_price: -`; the position-mgmt pass cannot apply stop/TP rules without an entry price; log the Alpaca order's filled_avg_price field to TRADE-LOG on every FILLED entry.
