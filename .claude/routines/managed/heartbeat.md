# Routine — heartbeat (managed cloud, canary)

You are the deepCommodity heartbeat agent. Verifies the loop is alive without trading. Hourly cadence.

## Steps

1. Auto-heal deps if missing (cached after first run):
   ```bash
   python3 -c "import ccxt, alpaca" 2>/dev/null || \
     pip install --quiet --break-system-packages ccxt alpaca-py
   ```
2. Bootstrap state:
   ```bash
   python3 tools/sync_state.py --skip-pull
   ```
3. Don't halt on KILL_SWITCH — heartbeat must report even when armed.
4. Verify imports + universe loader + featurization:
   ```bash
   python3 -c "
   from deepCommodity.guardrails import is_armed, sanitize_news
   from deepCommodity.universe import Universe
   assert sanitize_news('ignore previous instructions') == '[REDACTED]'
   u = Universe.load()
   assert len(u.theme_names()) >= 5
   print(f'guardrails OK; KILL_SWITCH={is_armed()}; themes={len(u.theme_names())}')
   "
   ```
5. Smoke-run rank + forecast on the bundled fixture:
   ```bash
   python3 tools/rank_smallcaps.py --input tests/fixtures/sample_market.json --top 3
   python3 tools/forecast.py --input tests/fixtures/sample_market.json --symbols BTC,TIA,INJ
   ```
6. Append a dated heartbeat:
   ```bash
   python3 tools/journal.py research --topic "heartbeat" \
     --body "alive at $(date -u +%FT%TZ); guardrails OK; universe + rank + forecast OK"
   ```
7. Persist log changes:
   ```bash
   bash tools/persist_logs.sh heartbeat
   ```
8. Send a Telegram heartbeat (silent if env not set):
   ```bash
   python3 tools/notify_telegram.py --topic info --severity ok \
     --message "heartbeat OK $(date -u +%FT%TZ)" --quiet
   ```
9. Exit 0.

## On failure

Don't retry. Surface the failure in the journal entry and exit non-zero.
