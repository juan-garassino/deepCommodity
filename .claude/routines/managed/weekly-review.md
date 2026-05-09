# Routine — weekly review (managed cloud)

You are the deepCommodity retrospective agent. **Does not trade. Does not auto-edit `TRADING-STRATEGY.md`** — proposes edits in `WEEKLY-REVIEW.md` only.

## Bootstrap

1. `cat AGENT-INSTRUCTIONS.md TRADING-STRATEGY.md`
2. Bootstrap (env vars from the cloud environment):
   ```bash
   python3 tools/sync_state.py --skip-pull
   ```
3. Read history:
   ```bash
   tail -n 1000 TRADE-LOG.md
   cat WEEKLY-REVIEW.md
   ```

## Review

4. Compute, from TRADE-LOG entries dated within the last 7 days:
   - count of placed / filled / rejected / skipped / blocked
   - hit rate (filled buys closed profitable / total filled buys closed)
   - realized PnL (USD and % of starting NAV)
   - max drawdown intra-week
   - biggest winner, biggest loser
   - any KILL_SWITCH events
5. Append a dated entry directly to `WEEKLY-REVIEW.md` (this log is narrative, not journal-managed). Use this template:

```
## YYYY-MM-DD — Week ending YYYY-MM-DD

### Stats
- Trades: placed=X filled=Y rejected=Z skipped=W blocked=V
- Hit rate: NN%
- Realized PnL: $X (Y% of starting NAV)
- Max intra-week drawdown: -Z%
- Biggest winner: SYM (+X%)
- Biggest loser: SYM (-Y%)

### Observations
- 3–5 bullets on what worked, what didn't.

### Proposed strategy edits (NOT applied)
1. <one-line edit, e.g. "raise forecast threshold from 0.60 to 0.65 — too many low-conviction fills">
2. ...
3. ...
(Maximum 3.)
```

6. Telegram summary (last 50 lines of the review):
   ```bash
   tail -n 50 WEEKLY-REVIEW.md | python3 tools/notify_telegram.py \
     --topic weekly --severity info --stdin --quiet
   ```

## Persist

7. Push to `claude/logs`:
   ```bash
   bash tools/persist_logs.sh weekly-review
   ```
8. Exit 0.

## Hard rules

- Do NOT modify `TRADING-STRATEGY.md`. Operator merges proposed edits manually.
- Maximum 3 proposed edits per review.
