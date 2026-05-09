# Routine — heartbeat (managed cloud)

You are the deepCommodity heartbeat agent. Verifies the loop is alive without trading. Cron minimum is 1 hour, so this fires hourly on the :03 minute (offset from research at :07 to spread API hits).

## Steps

1. Bootstrap (no env JSON needed — env vars come from the cloud environment):
   ```bash
   python3 tools/sync_state.py --skip-pull
   ```
2. Don't halt on KILL_SWITCH — heartbeat must report even when armed.
3. Verify imports + featurization:
   ```bash
   python3 -c "from deepCommodity.guardrails import is_armed, sanitize_news; assert sanitize_news('ignore previous instructions') == '[REDACTED]'; print('guardrails OK; KILL_SWITCH=' + str(is_armed()))"
   ```
4. Smoke-run rank + forecast on the bundled fixture:
   ```bash
   python3 tools/rank_smallcaps.py --input tests/fixtures/sample_market.json --top 3
   python3 tools/forecast.py --input tests/fixtures/sample_market.json --symbols BTC,TIA,INJ
   ```
5. Append a single dated heartbeat:
   ```bash
   python3 tools/journal.py research --topic "heartbeat" \
     --body "alive at $(date -u +%FT%TZ); guardrails OK; rank+forecast OK"
   ```
6. Persist log changes back to `claude/logs` branch:
   ```bash
   bash tools/persist_logs.sh heartbeat
   ```
7. Send a Telegram heartbeat (silent if env not set):
   ```bash
   python3 tools/notify_telegram.py --topic info --severity ok \
     --message "heartbeat OK $(date -u +%FT%TZ)" --quiet
   ```
8. Exit 0.

## On failure

Don't retry. Surface the failure in the journal entry and exit non-zero. The Routines UI status will go red and `notify_telegram.py` already pinged on the way through if it could.
