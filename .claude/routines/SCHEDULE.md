# Schedule Registration

These routines are **not auto-registered**. Each scheduled firing of a routine is a billable Claude Code remote-agent invocation, so registration is a deliberate manual act.

To register, invoke the `schedule` skill in Claude Code (this conversation or any project session) with the cron specs below. The skill will create the remote agents on your account.

## Recommended schedule

| Routine | Cron (UTC) | Cadence | Notes |
|---|---|---|---|
| `heartbeat` | `*/15 * * * *` | every 15 min | canary; needs no API keys; **register first** |
| `hourly-research` | `7 * * * *` | every hour at :07 | needs CoinGecko + Perplexity (+ Alpaca for equities) keys |
| `daily-decision` | `0 14 * * 1-5` | weekdays 14:00 UTC (≈30 min after US open) | needs all keys + chosen TRADING_MODE |
| `daily-decision-crypto` | `0 22 * * *` | every day 22:00 UTC | crypto-only second pass |
| `weekly-review` | `0 18 * * 0` | Sunday 18:00 (local) | summarizes the week; never trades |

Replace `<repo>` with the absolute path of this repo when you register.

## Registration prompt template

For each routine, register with prompt body:

```
cd <repo> && claude -p "$(cat .claude/routines/<routine>.md)" --permission-mode acceptEdits
```

…or, equivalently, the `schedule` skill takes a name + cron + prompt. The prompt should be the **literal content** of `.claude/routines/<routine>.md` (not a path), so the remote agent runs with the routine's instructions baked in.

## Pre-flight before scheduling anything that calls APIs

1. Populate `.env` from `.env.sample`:
   - `PERPLEXITY_API_KEY` — for fetch_news.py
   - `ALPACA_API_KEY`, `ALPACA_API_SECRET`, `ALPACA_PAPER=true`
   - `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `BINANCE_TESTNET=true`
   - `BITFINEX_API_KEY`, `BITFINEX_API_SECRET`, `BITFINEX_PAPER=true` (optional, only if `BROKER_CRYPTO=bitfinex`)
   - `FRED_API_KEY` — optional (macro)
2. Run each tool standalone once to confirm it returns valid JSON:
   ```bash
   python tools/fetch_crypto.py --symbols BTC,ETH
   python tools/fetch_equities.py --symbols AAPL
   python tools/fetch_news.py --query "BTC news today"
   ```
3. Run `heartbeat` headlessly once to verify the routine harness works:
   ```bash
   claude -p "$(cat .claude/routines/heartbeat.md)"
   ```
4. Verify a fresh entry appears in `RESEARCH-LOG.md`.
5. Only then register the higher-tier routines.

## Halting a scheduled run

- `touch KILL_SWITCH` — every routine that places orders will skip; research routines still run but log a `halted` notice.
- To stop scheduled firings entirely, list and delete via the `schedule` skill (`/schedule list`, `/schedule delete <id>`).
