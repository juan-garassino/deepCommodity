# Routine — daily decision (managed cloud)

You are the deepCommodity trading agent. **May place trades** in paper mode by default; live mode requires both `TRADING_MODE=live` AND `DAILY_DECISION_AUTHORIZE_LIVE=true` in the cloud environment.

## Bootstrap

1. `cat AGENT-INSTRUCTIONS.md TRADING-STRATEGY.md`
2. Bootstrap (env vars are pre-injected from the cloud environment):
   ```bash
   python3 tools/sync_state.py --skip-pull
   ```
3. Halt check:
   ```bash
   if [ -f KILL_SWITCH ]; then
     python3 tools/notify_telegram.py --topic halt --severity error \
       --message "daily-decision halted by KILL_SWITCH" --quiet
     exit 0
   fi
   ```
4. Recover recent state:
   ```bash
   tail -n 200 RESEARCH-LOG.md
   tail -n 200 TRADE-LOG.md
   ```

## Decide

5. Fresh data:
   ```bash
   python3 tools/fetch_crypto.py --symbols BTC,ETH,SOL,AVAX,LINK,ATOM,NEAR,INJ,FET,RNDR,TIA,JUP > /tmp/crypto.json
   python3 tools/fetch_equities.py --symbols AAPL,MSFT,NVDA,SOFI,PLTR,RKLB,IONQ,RXRX,ASTS > /tmp/equities.json
   python3 tools/fetch_news.py --query "today's market-moving events for crypto + US equities" > /tmp/news.json
   ```
6. Rank + forecast:
   ```bash
   python3 tools/rank_smallcaps.py --input /tmp/crypto.json --input /tmp/equities.json --top 8 > /tmp/ranked.json
   python3 tools/forecast.py --input /tmp/crypto.json --input /tmp/equities.json \
     --model rule-based > /tmp/forecasts.json
   ```
   (Once trained transformer checkpoints are in `data/models/<SYM>.pt`, switch to `--model ensemble --news-input /tmp/news.json`. Ensemble degrades gracefully if a checkpoint is missing for a symbol.)
7. For each candidate where **rank score ≥ 0.55 AND forecast confidence ≥ 0.60**:
   - direction `long` → buy; `short` → no shorts in v1, skip
   - size: `qty = min(0.05 × NAV, conviction × tier_sleeve_remaining) / current_price`
   - run `python3 tools/risk_check.py --symbol <s> --side buy --qty <q> --price <p> --asset-class crypto|equity`
     - exit 0 → proceed; non-zero → journal as `skipped` and move on
   - run `python3 tools/place_order.py --symbol <s> --side buy --qty <q> --price <p> --asset-class crypto|equity --reason "<one-line>"`
     - pass `--confirm-live` ONLY if `TRADING_MODE=live` AND `DAILY_DECISION_AUTHORIZE_LIVE=true`. Otherwise stay in paper.
8. Cap total new positions at 3 (`max_new_positions_per_day`).
9. Telegram end-of-day summary:
   ```bash
   python3 tools/notify_telegram.py --topic trade --severity info \
     --message "daily-decision: X placed, Y blocked, Z skipped (mode=$TRADING_MODE)" --quiet
   ```

## Persist

10. Push log changes:
    ```bash
    bash tools/persist_logs.sh daily-decision
    ```
11. Exit 0.

## Hard rules

- Never call `place_order.py` without first calling `risk_check.py` (must exit 0).
- Never call `place_order.py` if `KILL_SWITCH` exists.
- `place_order.py` already journals + Telegram-pings every outcome.
- If `TRADING_MODE=live` but `DAILY_DECISION_AUTHORIZE_LIVE` is unset, stay in paper.
