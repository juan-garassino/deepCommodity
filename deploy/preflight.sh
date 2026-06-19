#!/usr/bin/env bash
# Pre-flight gate — run AFTER populating .env, BEFORE enabling any trading timer.
#
# Verifies the VPS can actually trade crypto: Claude Code is installed + authed,
# Binance is reachable from this region (the whole reason for the VPS), .env is
# present + locked down with the required keys, and the broker libs import.
#
# Exits 0 only if every check passes; non-zero otherwise. Operator script —
# run from the shell as the trader user (not invoked by the agent):
#   sudo -u trader /srv/deepCommodity/deploy/preflight.sh

set -u

REPO="${REPO:-/srv/deepCommodity}"
ENV_FILE="${ENV_FILE:-$REPO/.env}"
FAIL=0

pass() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✗\033[0m %s\n' "$1"; FAIL=1; }

echo "── deepCommodity VPS preflight ──"

# Load .env so we can inspect keys (and pick up ANTHROPIC_API_KEY for the auth check).
if [ -f "$ENV_FILE" ]; then
  set -a; . "$ENV_FILE"; set +a
fi

# 1. Claude Code CLI present.
if command -v claude >/dev/null 2>&1; then
  pass "claude CLI on PATH ($(command -v claude))"
else
  fail "claude CLI not found on PATH — install_remote.sh installs it; check the trader user's PATH"
fi

# 2. Claude headless auth: subscription OAuth token, API key, or stored credentials.
if [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  pass "Claude auth: CLAUDE_CODE_OAUTH_TOKEN set (subscription)"
elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  pass "Claude auth: ANTHROPIC_API_KEY set"
elif [ -f "$HOME/.claude/.credentials.json" ] || [ -d "$HOME/.claude" ]; then
  pass "Claude auth: ~/.claude credentials present"
else
  fail "Claude not authenticated — set CLAUDE_CODE_OAUTH_TOKEN (from 'claude setup-token') or ANTHROPIC_API_KEY in .env, or run 'claude' login once as this user"
fi

# 3. Binance reachability — the decisive geo check (451 = wrong region, hard fail).
CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 https://api.binance.com/api/v3/ping 2>/dev/null || echo 000)"
if [ "$CODE" = "200" ]; then
  pass "Binance reachable (HTTP 200) — region OK"
elif [ "$CODE" = "451" ]; then
  fail "Binance HTTP 451 — this region is geo-blocked; crypto cannot execute here. Move to a Binance-allowed region."
else
  fail "Binance ping returned HTTP $CODE (expected 200) — check network/DNS"
fi

# 4. .env present, locked to 0600, required keys non-empty.
if [ ! -f "$ENV_FILE" ]; then
  fail ".env missing at $ENV_FILE — copy .env.sample and populate it"
else
  MODE="$(stat -c '%a' "$ENV_FILE" 2>/dev/null || stat -f '%Lp' "$ENV_FILE" 2>/dev/null || echo '?')"
  if [ "$MODE" = "600" ]; then pass ".env mode 600"; else fail ".env mode is $MODE (want 600): chmod 600 $ENV_FILE"; fi
  for k in TRADING_MODE BINANCE_API_KEY BINANCE_API_SECRET OPENAI_API_KEY; do
    if [ -n "$(eval "printf '%s' \"\${$k:-}\"")" ]; then pass ".env $k set"; else fail ".env $k is empty"; fi
  done
fi

# 5. Broker libs import.
if python3 -c "import ccxt, alpaca" 2>/dev/null; then
  pass "python deps import (ccxt, alpaca)"
else
  fail "python deps missing — run: pip install -r $REPO/requirements.txt"
fi

echo "──────────────────────────────────"
if [ "$FAIL" -eq 0 ]; then
  echo "PREFLIGHT PASS — safe to smoke-test (run_routine.sh decision) and enable timers."
  exit 0
else
  echo "PREFLIGHT FAIL — fix the ✗ items above before enabling any trading timer."
  exit 1
fi
