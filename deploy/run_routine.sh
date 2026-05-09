#!/usr/bin/env bash
# Run a deepCommodity routine in headless Claude Code.
#
# Usage:
#   ./deploy/run_routine.sh heartbeat
#   ./deploy/run_routine.sh hourly-research
#   ./deploy/run_routine.sh daily-decision
#   ./deploy/run_routine.sh weekly-review
#
# Designed to be called from cron / systemd. Streams output to logs/<routine>.log
# and pings Telegram on hard failure (claude exited non-zero) so cron silence
# never masks a broken loop.

set -u
ROUTINE="${1:-heartbeat}"
REPO="${REPO:-/srv/deepCommodity}"
LOG_DIR="${LOG_DIR:-$REPO/logs}"
ENV_FILE="${ENV_FILE:-$REPO/.env}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"

cd "$REPO" || { echo "REPO not found: $REPO" >&2; exit 2; }
mkdir -p "$LOG_DIR"

# Load .env into the environment (TELEGRAM_*, BINANCE_*, ALPACA_*, etc.).
if [ -f "$ENV_FILE" ]; then
  set -a; . "$ENV_FILE"; set +a
fi

PROMPT_FILE=".claude/routines/${ROUTINE}.md"
if [ ! -f "$PROMPT_FILE" ]; then
  echo "routine prompt not found: $PROMPT_FILE" >&2
  exit 3
fi

LOG="$LOG_DIR/${ROUTINE}.log"
TS="$(date -u +%FT%TZ)"
echo "── $TS  start $ROUTINE ──" >> "$LOG"

# Headless invocation. --permission-mode acceptEdits lets allowlisted bash run
# without prompts; everything outside the allowlist still blocks (fail-closed).
"$CLAUDE_BIN" -p "$(cat "$PROMPT_FILE")" \
  --permission-mode acceptEdits \
  >> "$LOG" 2>&1
EXIT=$?

echo "── $(date -u +%FT%TZ)  end $ROUTINE (exit=$EXIT) ──" >> "$LOG"

if [ "$EXIT" -ne 0 ]; then
  python3 "$REPO/tools/notify_telegram.py" \
    --topic halt --severity error \
    --message "routine $ROUTINE FAILED (exit=$EXIT). Last log lines: $(tail -n 5 "$LOG" | tr '\n' ' ')" \
    --quiet || true
fi

exit "$EXIT"
