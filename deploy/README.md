# Remote deployment

This directory contains everything needed to run the deepCommodity routines unsupervised on a Linux VPS, with Telegram status notifications.

> **Why a VPS (not the Anthropic cloud routines):** Binance geo-blocks the Anthropic cloud egress
> IP (HTTP 451), so crypto can't execute from cloud routines. The VPS must be in a **Binance-allowed
> region**. The VPS also makes the `KILL_SWITCH` a persistent local file every cron run sees (the
> cloud's stateless clones can't propagate it). **If you run the VPS, disable the cloud trading
> routines** (`dc decision`, `dc position-mgmt`) so the two don't double-execute.

Routines run from the prompts in `.claude/routines/managed/`. Active schedule (UTC): `decision`
every 4h, `position-mgmt` at 03/09/15/21, `weekly-review` Sunday 18:00 — see `crontab.template`.

## What "unsupervised" means here

Each routine is a markdown prompt under `.claude/routines/managed/`. A scheduler (cron or systemd) calls `deploy/run_routine.sh <name>`, which:

1. Loads `.env` (API keys, Telegram token).
2. Runs `claude -p "$(cat .claude/routines/managed/<name>.md)" --permission-mode acceptEdits` headless.
3. Streams stdout+stderr to `logs/<name>.log`.
4. On non-zero exit, pings Telegram with the last 5 log lines so cron silence never masks a broken loop.

Claude Code itself is the agent — there is no daemon, no event loop, no long-running gateway. Each routine fires, does its work, exits.

## Prereqs

- A Linux VPS (Ubuntu 22.04 or Debian 12 tested) **in a Binance-allowed region** (verify `curl -s -o /dev/null -w '%{http_code}' https://api.binance.com/api/v3/ping` returns `200`, not `451`). 1 vCPU + 1 GB RAM is enough for the rule-based forecaster path. Add 4 GB RAM if you want CPU inference of the trained transformer.
- An Anthropic API key (Claude Code uses your account).
- A Telegram bot token + your chat ID (see `tools/notify_telegram.py` docstring).
- API keys for whichever brokers/sources you need: Binance / Bitfinex / Alpaca / Perplexity / FRED.

## One-shot install (Ubuntu/Debian)

As root on the VPS, after pre-cloning the repo to `/srv/deepCommodity`:

```bash
sudo ./deploy/install_remote.sh /srv/deepCommodity
```

The script:
- installs python, node, claude-code CLI
- creates a `trader` user (or reuses `$TRADER_USER`)
- copies `.env.sample` → `.env` (mode 0600)
- installs all systemd unit files + timers
- enables only the heartbeat timer (other timers stay off until you populate `.env`)

## Step-by-step manual install

```bash
# 1. clone (or rsync) the repo
git clone <repo-url> /srv/deepCommodity
cd /srv/deepCommodity

# 2. python deps
pip install -r requirements.txt

# 3. install Claude Code
npm install -g @anthropic-ai/claude-code

# 4. populate env
cp .env.sample .env
chmod 600 .env
$EDITOR .env

# 5. test the heartbeat manually
./deploy/run_routine.sh heartbeat
tail -n 30 logs/heartbeat.log

# 6. install timers
sudo cp deploy/systemd/*.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now deepcommodity-heartbeat.timer
```

## Scheduling: systemd vs cron

> **Note:** the new 24/7 schedule uses routines `decision`, `position-mgmt`, `weekly-review`.
> `crontab.template` is already updated for these — **cron is the quickest path**. The bundled
> `deploy/systemd/*` unit files still carry the legacy routine names (heartbeat/hourly-research/
> daily-decision); regenerate them for the new names if you prefer systemd.

Both are wired. **Prefer systemd** — better state visibility (`systemctl status …`), failed-run accounting, sandboxing.

### systemd (recommended)

```bash
sudo systemctl enable --now deepcommodity-heartbeat.timer
sudo systemctl enable --now deepcommodity-hourly-research.timer   # only after .env populated
sudo systemctl enable --now deepcommodity-daily-decision.timer
sudo systemctl enable --now deepcommodity-weekly-review.timer

# observe
systemctl list-timers 'deepcommodity-*'
journalctl -u 'deepcommodity@*.service' -f
```

The unit files apply OS-level sandboxing: `ProtectSystem=strict`, `ReadWritePaths=/srv/deepCommodity`, `ProtectHome=read-only`, `NoNewPrivileges=true`. The agent cannot escape the repo even if it tries.

### cron (alternative)

```bash
crontab -e
# paste the contents of deploy/crontab.template
```

No sandboxing, but identical scheduling behavior. Use this only if your VPS does not run systemd.

## Halting

Three layers, in increasing severity:

| Action | Effect |
|---|---|
| Set `DC_HALT=true` in `.env` (or `TRADING_MODE=halt`) | Every order fail-closes on the next run — the reliable, fastest lever; no file, no restart |
| `touch /srv/deepCommodity/KILL_SWITCH` | Same effect via the repo-root file; persistent across cron runs on the VPS |
| `crontab -e` and comment the lines (or `sudo systemctl disable --now 'deepcommodity-*.timer'`) | Stop the schedule entirely |

On the VPS, `KILL_SWITCH` is a persistent local file, so every cron run sees it (unlike the cloud). The drawdown breaker (`tools/check_drawdown.py`, run by `position-mgmt`) auto-arms it only on a **real measured** −4% daily / −8% weekly drawdown and pings Telegram — it no longer arms merely because NAV is briefly unreadable (orders fail-close on that independently).

## Telegram

`tools/notify_telegram.py` is invoked from inside routines and from `place_order.py`. No bot framework, no webhook — just a `requests.post` to Telegram's `sendMessage` REST endpoint.

Setup once:

1. Talk to `@BotFather` on Telegram → `/newbot` → save token.
2. DM your new bot once.
3. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `from.id`.
4. Put both in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_CHAT_ID=...
   ```

You'll get pings for:
- every order outcome (filled / placed / blocked / rejected)
- every routine failure (non-zero exit from `run_routine.sh`)
- KILL_SWITCH armed (auto by circuit breaker, or manual)
- end-of-day decision summary
- weekly review

If `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` are unset, all notify calls silently no-op — the routines never fail because Telegram is down.

## Logs

```
/srv/deepCommodity/logs/
  heartbeat.log
  hourly-research.log
  daily-decision.log
  weekly-review.log
```

Append-only; rotate with `logrotate` if size matters. Each routine writes its append-only entries to the markdown logs (`RESEARCH-LOG.md`, `TRADE-LOG.md`, `WEEKLY-REVIEW.md`) which are also git-trackable for audit.

## Smoke-testing remotely

```bash
sudo -u trader /srv/deepCommodity/deploy/run_routine.sh heartbeat
tail -n 30 /srv/deepCommodity/logs/heartbeat.log
```

If the heartbeat fails, the timers won't stop firing — fix the underlying issue first, then `systemctl reset-failed deepcommodity@heartbeat.service`.
