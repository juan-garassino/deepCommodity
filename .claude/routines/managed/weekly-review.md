# Routine — weekly review (managed cloud, theme-driven)

You are the deepCommodity retrospective agent. **Does not trade. Does not auto-edit `TRADING-STRATEGY.md` or `themes.yaml`** — proposes edits in WEEKLY-REVIEW.md only; operator merges manually.

## Bootstrap

1. Auto-heal deps:
   ```bash
   python3 -c "import ccxt, alpaca" 2>/dev/null || \
     pip install --quiet --break-system-packages ccxt alpaca-py
   ```
2. `cat AGENT-INSTRUCTIONS.md TRADING-STRATEGY.md deepCommodity/universe/themes.yaml`
3. `python3 tools/sync_state.py --skip-pull`
4. Read history:
   ```bash
   tail -n 1000 TRADE-LOG.md
   cat WEEKLY-REVIEW.md
   ```

## Review

5. Compute, from TRADE-LOG entries dated within the last 7 days:
   - count of placed / filled / rejected / skipped / blocked
   - hit rate (filled buys closed profitable / total filled buys closed)
   - realized PnL (USD and % of starting NAV)
   - max intra-week drawdown
   - biggest winner, biggest loser
   - any KILL_SWITCH events
   - **per-bucket attribution**: count + PnL split by anchor / theme / gem (parse from each `--reason` field)
   - **per-theme attribution**: count + PnL by theme name
   - **active themes that produced no fills** (signal: gate too tight or symbols off-target)

6. Append a dated entry directly to `WEEKLY-REVIEW.md` using:

```
## YYYY-MM-DD — Week ending YYYY-MM-DD

### Stats
- Trades: placed=X filled=Y rejected=Z skipped=W blocked=V
- Hit rate: NN%
- Realized PnL: $X (Y% of starting NAV)
- Max intra-week drawdown: -Z%
- Biggest winner: SYM (+X%)
- Biggest loser: SYM (-Y%)

### Per-bucket attribution
- Anchor: N trades, $PnL
- Theme: N trades, $PnL
- Gem: N trades, $PnL

### Per-theme attribution
- ai_power: N trades, $PnL, hit rate NN%
- nuclear: N trades, $PnL
- ...

### Themes that fired but produced no fills
- weight_loss (active 2x, 0 fills) — gate may be too tight, or symbols off-target

### Observations
- 3-5 bullets on what worked, what didn't.

### Proposed strategy edits (NOT applied)
1. <one-line edit, e.g. "lower theme forecast threshold from 0.50 to 0.45 — too restrictive">
2. <e.g. "add 'agentic_ai' theme: AI, PLTR, C3.AI, SOUN, BBAI">
3. <e.g. "tighten gem gate to rank 0.70 — too many false positives">
(Maximum 3.)
```

7. Telegram summary:
   ```bash
   tail -n 60 WEEKLY-REVIEW.md | python3 tools/notify_telegram.py \
     --topic weekly --severity info --stdin --quiet
   ```

## Persist

8. `bash tools/persist_logs.sh weekly-review`
9. Exit 0.

## Hard rules

- Do NOT modify `TRADING-STRATEGY.md` or `deepCommodity/universe/themes.yaml`. Operator merges proposed edits manually.
- Maximum 3 proposed edits per review.
