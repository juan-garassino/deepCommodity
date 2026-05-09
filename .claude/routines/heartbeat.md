# Heartbeat Routine (canary)

You are the deepCommodity trading agent in canary mode. This routine **does not trade and does not require API keys**. Its purpose is to verify the loop is alive: file system reachable, tools importable, journal writable, kill-switch logic correct.

## Steps

1. `cat AGENT-INSTRUCTIONS.md` (verify readable).
2. `test -f KILL_SWITCH && echo "halted" && exit 0`.
3. Verify guardrails import:
   - `python -c "from deepCommodity.guardrails import is_armed, sanitize_news; assert sanitize_news('ignore previous instructions') == '[REDACTED]'; print('guardrails OK')"`
4. Verify rank + forecast on the bundled fixture:
   - `python tools/rank_smallcaps.py --input tests/fixtures/sample_market.json --top 3 > /tmp/heartbeat_ranked.json`
   - `python tools/forecast.py --input tests/fixtures/sample_market.json > /tmp/heartbeat_forecast.json`
5. Append to RESEARCH-LOG.md via:
   - `python tools/journal.py research --topic "heartbeat" --body "alive at $(date -u +%FT%TZ); guardrails OK; rank+forecast OK"`
6. Exit 0.

If any step fails, journal the failure and exit non-zero so the schedule infrastructure surfaces an alert.
