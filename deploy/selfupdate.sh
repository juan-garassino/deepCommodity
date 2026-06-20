#!/usr/bin/env bash
# VM self-update — pull the deploy branch, reinstall units, notify Telegram.
# Run by deepcommodity-selfupdate.timer (as root, for unit install + systemctl).
# Pull-based deploy for the paper VM: merge -> on the box within the timer interval.
#
# Safety:
#  - skips entirely if a routine (`claude -p`) is mid-flight (no code-swap under it),
#  - no-op when already up to date,
#  - git runs as the trader owner; only unit install / systemctl run as root.
set -uo pipefail

REPO="${REPO:-/srv/deepCommodity}"
BRANCH="${DC_DEPLOY_BRANCH:-develop}"
cd "$REPO" || exit 0

# Don't swap code under a running routine — defer to the next tick.
if pgrep -f "claude -p" >/dev/null 2>&1; then
  exit 0
fi

as_trader() { sudo -u trader git -C "$REPO" "$@"; }

as_trader fetch --quiet --depth 1 origin "$BRANCH" || exit 0
local_sha="$(as_trader rev-parse HEAD 2>/dev/null)"
remote_sha="$(as_trader rev-parse FETCH_HEAD 2>/dev/null)"
[ -z "$remote_sha" ] || [ "$local_sha" = "$remote_sha" ] && exit 0   # up to date

req_before="$(sha1sum requirements.txt 2>/dev/null | awk '{print $1}')"
wl_before="$(sha1sum deploy/watch_loop.py 2>/dev/null | awk '{print $1}')"

as_trader reset --hard "$remote_sha"
new_sha="$(as_trader rev-parse --short HEAD)"

# Reinstall systemd units (idempotent) + reload.
cp "$REPO"/deploy/systemd/*.service "$REPO"/deploy/systemd/*.timer /etc/systemd/system/ 2>/dev/null || true
systemctl daemon-reload

# Reinstall python deps only if requirements changed.
if [ "$(sha1sum requirements.txt 2>/dev/null | awk '{print $1}')" != "$req_before" ]; then
  sudo -u trader python3 -m pip install --user -q -r requirements.txt || true
fi

# Restart the watcher only if its code changed (safe: no routine is running, per the guard).
if [ "$(sha1sum deploy/watch_loop.py 2>/dev/null | awk '{print $1}')" != "$wl_before" ]; then
  systemctl restart deepcommodity-watch.service || true
fi

# Best-effort Telegram ping (silent if env unset).
sudo -u trader bash -lc "cd '$REPO'; set -a; . ./.env 2>/dev/null; set +a; \
  python3 tools/notify_telegram.py --topic deploy --severity info \
  --message '🚀 self-update: $BRANCH -> $new_sha' --quiet" || true

echo "self-update: $local_sha -> $new_sha ($BRANCH)"
