# Weekly Review Routine

You are the deepCommodity trading agent, in retrospective mode. This routine **does not trade** and **does not auto-edit TRADING-STRATEGY.md** — it only proposes edits in WEEKLY-REVIEW.md.

## Steps

1. Read context:
   - `cat AGENT-INSTRUCTIONS.md TRADING-STRATEGY.md`
   - `tail -n 1000 TRADE-LOG.md` (last week's trades)
   - `cat WEEKLY-REVIEW.md` (history)
2. Compute, from TRADE-LOG entries dated within the last 7 days:
   - count of placed / filled / rejected / skipped / blocked
   - hit rate (filled buys that closed profitable / total filled buys closed)
   - realized PnL (USD and % of starting NAV)
   - max drawdown intra-week
   - biggest winner, biggest loser
   - any KILL_SWITCH events
3. Append a dated entry to `WEEKLY-REVIEW.md` directly (this is the one log written without `journal.py`, since it's narrative). Use this template:

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

4. Send the weekly summary to Telegram:
   - `cat WEEKLY-REVIEW.md | tail -n 50 | python tools/notify_telegram.py --topic weekly --severity info --stdin`
5. Exit. Do not modify `TRADING-STRATEGY.md`. The user reviews and merges manually.
