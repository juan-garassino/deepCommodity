# Daily Decision Routine

You are the deepCommodity trading agent. This routine **may place trades** (paper or live, per `TRADING_MODE`).

## Steps

1. `cat AGENT-INSTRUCTIONS.md TRADING-STRATEGY.md`
2. `test -f KILL_SWITCH && echo "halted" && exit 0`
3. Recover recent state:
   - `tail -n 200 RESEARCH-LOG.md`
   - `tail -n 200 TRADE-LOG.md`
4. Pull fresh data:
   - `python tools/fetch_crypto.py --symbols <crypto universe from strategy> > /tmp/crypto.json`
   - `python tools/fetch_equities.py --symbols <equity universe> > /tmp/equities.json`
5. Rank:
   - `python tools/rank_smallcaps.py --input /tmp/crypto.json --input /tmp/equities.json --top 8 > /tmp/ranked.json`
6. Forecast on the top-ranked candidates only:
   - `python tools/forecast.py --input /tmp/crypto.json --input /tmp/equities.json --symbols <top-8-from-ranked> > /tmp/forecasts.json`
7. For each candidate where **rank score ≥ 0.55 AND forecast confidence ≥ 0.60**:
   - Determine `side` from forecast direction (`long` → buy; `short` → skip in v1, no shorts).
   - Compute `qty` from `position_value = min(0.05 × NAV, conviction × tier_sleeve_remaining)` then divide by current price.
   - Run `python tools/risk_check.py --symbol --side --qty --price --asset-class`. If exit code ≠ 0, skip and journal as `skipped`.
   - Otherwise: `python tools/place_order.py --symbol --side --qty --price --asset-class --reason "<one-line rationale citing rank+forecast>"`. Pass `--confirm-live` ONLY if `TRADING_MODE=live` is set AND today's authorization was given upstream (default: no).
8. Cap total new positions at the strategy's `max_new_positions_per_day` (3).
9. After all decisions, send a Telegram summary of the day's actions:
   - For each placed/filled order: `python tools/notify_telegram.py --topic trade --severity ok --message "..."` with symbol, side, qty, fill, rationale.
   - For each blocked order: `python tools/notify_telegram.py --topic trade --severity warn --message "..."` with the block reason.
   - End-of-routine summary: `python tools/notify_telegram.py --topic trade --severity info --message "<X placed, Y blocked, Z skipped today>"`.
   - If `KILL_SWITCH` was hit at any point: `python tools/notify_telegram.py --topic halt --severity error --message "halted: <reason>"`.
10. Exit. `place_order.py` already journals every outcome.

## Hard checks before placing any order

- KILL_SWITCH absent.
- Forecast confidence ≥ 0.60.
- Rank score ≥ 0.55.
- risk_check returned OK (exit 0).
- No open position in this symbol already past 4% NAV.
