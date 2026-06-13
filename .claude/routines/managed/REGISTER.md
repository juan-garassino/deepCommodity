# Registering deepCommodity routines on Claude Code

Per [the official routines docs](https://code.claude.com/docs/en/routines), routines run on Anthropic-managed cloud infrastructure. Two registration paths:

- **CLI** (`/schedule`) — fastest. Run from any Claude Code session.
- **Web** (`claude.ai/code/routines`) — visual, useful for non-schedule triggers (API, GitHub events).

This guide covers both. The CLI path is recommended for our four scheduled routines.

---

## One-time setup (in this order)

### 1. Push the repo to GitHub

The cloud sandbox `git clone`s the repo each run. Make sure your fork is pushed and reachable.

### 2. Configure the cloud environment

Cloud environments are managed at `claude.ai/code/environments` (or via the **Edit routine → Environment** picker). Create or edit one named `deepCommodity` with:

**Environment variables** — paste in:
```
# --- control plane (code-enforced) ---
TRADING_MODE=paper                 # paper | live | halt
DAILY_DECISION_AUTHORIZE_LIVE=false
DC_HALT=false                      # set true to halt ALL orders on the next run (out-of-band kill)
DC_MAX_NAV_USD=500                 # hard ceiling on live NAV; required (>0) before any live order

# --- brokers (REQUIRED to trade) ---
BINANCE_API_KEY=...                # crypto; testnet keys for paper
BINANCE_API_SECRET=...
BINANCE_TESTNET=true               # false only when going live
ALPACA_API_KEY=...                 # equities; PAPER keypair for paper
ALPACA_API_SECRET=...
ALPACA_PAPER=true                  # false only when going live (separate LIVE keypair)
# Bitfinex is DISABLED in the live path (audit B7) — do not configure it.

# --- signal sources ---
OPENAI_API_KEY=...                 # REQUIRED — news/signal engine (~$0.04/call)
FINNHUB_API_KEY=...                # recommended (free) — earnings calendar
FRED_API_KEY=...                   # recommended (free) — macro + FedWatch
CRYPTOQUANT_API_KEY=...            # optional — on-chain (falls back to Binance volume)
COINGECKO_API_KEY=...              # optional — raises CoinGecko rate limits

# --- alerts + commits (optional) ---
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
GIT_BOT_EMAIL=bot@deepcommodity.local
GIT_BOT_NAME=deepCommodity-bot
```

**Setup script** — paste the contents of `.claude/routines/managed/setup.sh`:
```bash
set -e
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r requirements.txt
echo "deepCommodity environment ready"
```
The result is cached, so it doesn't re-run every routine fire.

**Network access** → **Custom**. Add these domains to the allowlist (Trusted defaults block them):

```
api.binance.com
api.coingecko.com
api.alpaca.markets
paper-api.alpaca.markets
data.alpaca.markets
api.telegram.org
api.openai.com
api.stlouisfed.org
api.finnhub.io
api.cryptoquant.com
www.sec.gov
openinsider.com
query2.finance.yahoo.com
fc.yahoo.com
```
(Bitfinex hosts are no longer needed — the venue is disabled in the live path.)

Tick **Also include default list of common package managers** so `pip install` still works.

### 3. GitHub branch policy

Routines push to `claude/`-prefixed branches by default — that matches our `claude/logs` log branch, so **don't** enable "Allow unrestricted branch pushes". Logs land safely on `claude/logs`; merge into main on your own cadence.

### 4. Telegram bot

If you haven't already: DM `@BotFather`, `/newbot`, save token. DM the new bot once. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates`, copy `from.id`. Both go in the environment vars above.

---

## Replacing / updating existing routines

A routine stores a COPY of its instructions at registration time — it does **not** re-read the
`.md` from the repo each run. So after the prompts change (e.g. the live-readiness/refactor
passes), you must push the new instructions into each routine:

1. **Update the cloud environment first** (env vars + network allowlist above) — the new control
   vars (`DC_HALT`, `DC_MAX_NAV_USD`) and the six-stream hosts (`api.finnhub.io`,
   `api.cryptoquant.com`, `www.sec.gov`, `openinsider.com`) are required.
2. **Update each routine's instructions** to the current `.claude/routines/managed/<name>.md`:
   `/schedule update <routine>` (CLI), or web UI → **Edit routine → Instructions** → repaste.
3. **Add the new `dc position-mgmt` routine** (cron `0 13,21 * * *`) — it didn't exist before the
   live-readiness pass; it runs the drawdown breaker and closes/​trails but never opens.

## Register the routines

### Path A — CLI (recommended)

In any Claude Code session connected to your account, run:

```text
/schedule daily at 14:00 UTC and 22:00 UTC, run the deepCommodity daily decision routine using the prompt at .claude/routines/managed/daily-decision.md against repo deepCommodity, environment deepCommodity
```

Claude walks you through the rest. Repeat for each routine:

| Routine | Natural-language schedule prompt |
|---|---|
| `dc heartbeat` | `/schedule hourly at :03, run the deepCommodity heartbeat routine using the prompt at .claude/routines/managed/heartbeat.md, repo deepCommodity, environment deepCommodity` |
| `dc hourly research` | `/schedule hourly at :07, run the deepCommodity hourly research routine using the prompt at .claude/routines/managed/hourly-research.md, repo deepCommodity, environment deepCommodity` |
| `dc daily decision` | (the example above) |
| `dc position-mgmt` | `/schedule daily at 13:00 UTC and 21:00 UTC, run the deepCommodity position-mgmt routine using the prompt at .claude/routines/managed/position-mgmt.md, repo deepCommodity, environment deepCommodity` |
| `dc weekly review` | `/schedule Sundays at 18:00 UTC, run the deepCommodity weekly review routine using the prompt at .claude/routines/managed/weekly-review.md, repo deepCommodity, environment deepCommodity` |

Manage them after the fact:
- `/schedule list` — see all registered routines
- `/schedule update` — edit a routine
- `/schedule run` — fire one immediately

> **Note**: cron minimum is 1 hour, so the heartbeat is hourly (not 15-min). For fine-grained smoke testing, use `/schedule run` to fire manually.

### Path B — Web UI (claude.ai/code/routines)

Per routine:

1. **+ New routine**.
2. **Name**: `dc heartbeat` / `dc hourly research` / `dc daily decision` / `dc weekly review`.
3. **Instructions**: paste the entire body of the corresponding `.claude/routines/managed/<name>.md` file.
4. **Repository**: select your `deepCommodity` repo.
5. **Environment**: select the `deepCommodity` environment created in step 2 above.
6. **Trigger → Schedule**: set the cron string from the table below.
7. **Connectors**: remove all (none of the routines need them — env vars come from the environment, not Drive).
8. **Allow unrestricted branch pushes**: leave OFF — `persist_logs.sh` writes to `claude/logs` which is allowed by default.
9. **Create**.

| Routine | Cron (UTC) |
|---|---|
| `dc heartbeat` | `3 * * * *` |
| `dc hourly research` | `7 * * * *` |
| `dc daily decision` | `0 14 * * 1-5` (and create a second routine with `0 22 * * *` pointing at the same prompt) |
| `dc position-mgmt` | `0 13,21 * * *` |
| `dc weekly review` | `0 18 * * 0` |

---

## Verification

After creating the routines:

1. From the routine detail page, click **Run now** on `dc heartbeat`.
2. The session opens. Wait for it to finish (~30 s).
3. Confirm:
   - The transcript shows `guardrails OK` and `rank+forecast OK`.
   - A new commit appears on the `claude/logs` branch with message `heartbeat: <UTC stamp>`.
   - You receive a Telegram ping `✅ deepCommodity / info ... heartbeat OK`.
4. If the GitHub branch update is missing: check **Permissions → Allow unrestricted branch pushes** is OFF (we WANT this off — `claude/logs` is allowed by default; turning it on would let routines push anywhere).
5. If Telegram is missing: confirm `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in the environment, not in `.env`.

---

## Halting

| Action | Effect |
|---|---|
| **Set `DC_HALT=true` (or `TRADING_MODE=halt`) in the cloud environment** | **Primary kill switch for cloud routines.** Reaches the next run regardless of git state; the gate fails closed. This is the reliable one — prefer it. |
| Push an empty `KILL_SWITCH` file to `claude/logs` | Also blocks, but only if the run's git pull picks it up — use the env halt above as the dependable path. The drawdown breaker (`check_drawdown.py`, run by position-mgmt) auto-arms `KILL_SWITCH` on −4%d/−8%w. |
| Toggle a routine off (Routines UI) | Stops only that schedule; others continue. |
| Delete a routine | Permanent removal; past run sessions remain in your session list. |

`persist_logs.sh` includes `KILL_SWITCH` in its staged files, so when a routine commits its outputs, an existing kill switch propagates to the log branch automatically.

---

## Trade-offs vs VPS deploy (`deploy/`)

| | Managed routines | VPS + systemd |
|---|---|---|
| Infra to manage | none | $5–10/mo VPS |
| Secret storage | cloud environment (encrypted at rest by Anthropic) | local `.env` (mode 0600) |
| Cold start per run | ~5–10 s (clone + setup-script-cached) | <1 s |
| Log persistence | `git push` to `claude/logs` | local file append |
| Min cron interval | 1 hour | 1 minute |
| Max cron frequency | bounded by daily run cap | unlimited |
| Routine session UI | claude.ai/code/sessions (rich transcript) | `journalctl` + Telegram only |
| Failure surfaces | Routines list status + Telegram | systemd unit status + Telegram |
| Right call when… | you want zero ops | you need sub-minute latency, or many routines, or audit-grade local logging |

For v1: **start with managed**. You can always migrate later by populating `.env` from the env-var list above and following `deploy/README.md`.
