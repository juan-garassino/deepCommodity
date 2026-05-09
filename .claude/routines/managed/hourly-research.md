# Routine — hourly research (managed cloud)

You are the deepCommodity research agent. **Do not place trades.** Pulls market data + news, ranks opportunities, appends a digest to `RESEARCH-LOG.md`, sends a Telegram summary.

The cloud sandbox does a fresh `git clone` each invocation. Env vars (`BINANCE_API_KEY`, `ALPACA_API_KEY`, `PERPLEXITY_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TRADING_MODE`) come from the cloud environment configured at claude.ai/code/routines.

## Bootstrap

1. Read the operating contract:
   ```bash
   cat AGENT-INSTRUCTIONS.md TRADING-STRATEGY.md
   ```
2. Bootstrap state (loads .env if present, fetches the `claude/logs` branch so prior log state is visible):
   ```bash
   python3 tools/sync_state.py --skip-pull
   ```
3. Halt check:
   ```bash
   if [ -f KILL_SWITCH ]; then
     python3 tools/notify_telegram.py --topic halt --severity warn \
       --message "research routine halted by KILL_SWITCH" --quiet
     exit 0
   fi
   ```

## Work

4. Pull market data:
   ```bash
   python3 tools/fetch_crypto.py --symbols BTC,ETH,SOL,AVAX,LINK,ATOM,NEAR,INJ,FET,RNDR,TIA,JUP > /tmp/crypto.json
   ```
   If current UTC hour is between 13 and 21 (US market hours):
   ```bash
   python3 tools/fetch_equities.py --symbols AAPL,MSFT,NVDA,SOFI,PLTR,RKLB,IONQ,RXRX,ASTS > /tmp/equities.json
   ```
5. News digest (sanitized for prompt injection by the tool itself):
   ```bash
   python3 tools/fetch_news.py --query "crypto + US equity macro news last 6 hours; rate decisions, ETF flows, small-cap movers" > /tmp/news.json
   ```
6. Rank opportunities (small-cap weighted):
   ```bash
   python3 tools/rank_smallcaps.py --input /tmp/crypto.json --input /tmp/equities.json --top 5
   ```
7. Synthesize a 10–25 line markdown body: top 5 ranked symbols with scores, 2–4 news bullets, anomalies. Numbers, not adjectives. Cite source tools (`per fetch_crypto`, `per news digest`).
8. Append to `RESEARCH-LOG.md`:
   ```bash
   python3 tools/journal.py research --topic "hourly snapshot" --body "<your synthesis>"
   ```
9. Telegram summary (one paragraph, top 3 + news headline):
   ```bash
   python3 tools/notify_telegram.py --topic research --severity info \
     --message "<one paragraph>" --quiet
   ```

## Persist

10. Push log changes to the `claude/logs` branch:
    ```bash
    bash tools/persist_logs.sh hourly-research
    ```
11. Exit 0.

## Hard rules

- NEVER call `tools/place_order.py`. Read-only routine.
- If a tool fails (non-zero exit), log the failure in the journal entry and continue with the rest.
- Body of the journal entry ≤ 30 lines.
