#!/usr/bin/env bash
# One-shot remote provisioning.
#
# Tested on Ubuntu 22.04 / Debian 12. Run as root or with sudo.
# Idempotent — re-running upgrades the checkout and syncs systemd units.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/<you>/deepCommodity/master/deploy/install_remote.sh | sudo bash -s -- /srv/deepCommodity
# or, after cloning manually:
#   sudo ./deploy/install_remote.sh /srv/deepCommodity

set -euo pipefail

REPO_DIR="${1:-/srv/deepCommodity}"
USER_NAME="${TRADER_USER:-trader}"
REPO_URL="${REPO_URL:-}"   # set via env if you want install to git clone for you

echo "── installing system packages ──"
apt-get update -y
apt-get install -y --no-install-recommends \
  python3 python3-pip python3-venv git curl ca-certificates \
  build-essential

echo "── ensuring user ${USER_NAME} ──"
id -u "$USER_NAME" >/dev/null 2>&1 || useradd -m -s /bin/bash "$USER_NAME"

echo "── installing Claude Code CLI (npm) ──"
if ! command -v claude >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
  apt-get install -y nodejs
  npm install -g @anthropic-ai/claude-code
fi

echo "── ensuring repo at ${REPO_DIR} ──"
if [ ! -d "$REPO_DIR/.git" ]; then
  if [ -z "$REPO_URL" ]; then
    echo "  REPO_URL env not set and $REPO_DIR is not a git checkout" >&2
    echo "  either pre-clone the repo at $REPO_DIR or pass REPO_URL=git@..." >&2
    exit 2
  fi
  git clone "$REPO_URL" "$REPO_DIR"
else
  git -C "$REPO_DIR" pull --ff-only
fi
chown -R "$USER_NAME:$USER_NAME" "$REPO_DIR"
chmod +x "$REPO_DIR/deploy/run_routine.sh"

echo "── installing python deps ──"
sudo -u "$USER_NAME" python3 -m pip install --user -q -r "$REPO_DIR/requirements.txt"

echo "── seeding .env if missing ──"
if [ ! -f "$REPO_DIR/.env" ]; then
  cp "$REPO_DIR/.env.sample" "$REPO_DIR/.env"
  chown "$USER_NAME:$USER_NAME" "$REPO_DIR/.env"
  chmod 600 "$REPO_DIR/.env"
  echo "  ⚠ filled $REPO_DIR/.env from template — populate keys before enabling timers!"
fi

echo "── installing systemd units ──"
install -m 0644 "$REPO_DIR/deploy/systemd/"*.service /etc/systemd/system/ || true
install -m 0644 "$REPO_DIR/deploy/systemd/"*.timer /etc/systemd/system/
systemctl daemon-reload

echo "── enabling heartbeat timer (always on) ──"
systemctl enable --now deepcommodity-heartbeat.timer

echo
echo "  Install complete."
echo
echo "  Next steps:"
echo "    1. Authenticate Claude Code (ANTHROPIC_API_KEY in .env, or 'claude' login as $USER_NAME)"
echo "    2. Edit $REPO_DIR/.env with your API keys"
echo "    3. Gate before enabling any trading timer:"
echo "         sudo -u $USER_NAME $REPO_DIR/deploy/preflight.sh   # must PASS (Binance must read 200)"
echo "    4. Enable the trading timers when preflight is green:"
echo "         systemctl enable --now deepcommodity-decision.timer"
echo "         systemctl enable --now deepcommodity-position-mgmt.timer"
echo "         systemctl enable --now deepcommodity-weekly-review.timer"
echo "    5. Watch logs: journalctl -u 'deepcommodity@*.service' -f"
echo "    6. Stop everything: touch $REPO_DIR/KILL_SWITCH  (orders blocked)"
echo "       or: systemctl disable --now 'deepcommodity-*.timer'  (full halt)"
