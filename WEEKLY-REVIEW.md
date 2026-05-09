# WEEKLY-REVIEW.md

Weekly retrospective written by the Sunday-evening routine. Each entry summarizes the prior week's performance and proposes (does not auto-apply) up to 3 strategy edits.

---

## 2026-05-09 — Week ending 2026-05-09

### Stats
- Trades: placed=5 filled=1 rejected=1 skipped=0 blocked=3
- Hit rate: N/A (0 closed positions this week)
- Realized PnL: $0.00 (N/A% of starting NAV — no closed trades)
- Max intra-week drawdown: N/A (no closed positions)
- Biggest winner: N/A
- Biggest loser: N/A

### Observations
- KILL_SWITCH was armed during at least two BTC paper buy attempts (2026-05-09 10:51 and 11:02 UTC), blocking all crypto order flow for that period. No disarm event is recorded in the log, making it impossible to pinpoint how long the halt lasted.
- A live-mode BTC order was attempted without the required `--confirm-live` flag and was correctly rejected by the adapter — guardrail worked as designed.
- The first AAPL paper order failed with Alpaca auth error (HTTP 401, code 40110000); the same order succeeded nine minutes later, suggesting a transient credential or session issue, not a permanent misconfiguration.
- The single FILLED trade (AAPL paper) has `fill_price: -`, breaking PnL tracking for any future close of that position. No signals from the forecaster or ranker appear in this week's logs — all activity was smoke-test / system-validation, not alpha-driven.
- Zero alpha-generating trades were executed this week; the system is still in paper-trading shakedown (Phase 3) and the operational focus was integration testing rather than signal generation.

### Proposed strategy edits (NOT applied)
1. Require `tools/journal.py` to emit a timestamped KILL_SWITCH-armed and KILL_SWITCH-disarmed entry to TRADE-LOG.md whenever `KILL_SWITCH` is created or removed, so halt duration is always auditable.
2. Add a single immediate retry with re-authentication in `deepCommodity/execution/alpaca_adapter.py` on HTTP 401 before escalating to REJECTED status, to handle transient session expiry without dropping paper orders.
3. Make `fill_price` mandatory (non-nullable) in `tools/place_order.py` paper-mode path; if the broker returns no fill price, record the last-known mid-price and flag it as `fill_price_estimated: true` so PnL tracking remains intact.
