#!/usr/bin/env python3
"""deepCommodity reactive watcher — continuous, cheap, catalyst-driven.

Runs as an always-on systemd service (deepcommodity-watch.service). Each tick
(DC_WATCH_POLL_SEC) it cheaply polls crypto prices for free (CoinGecko via
tools/fetch_crypto.py) and fires a full `decision` routine pass ONLY when there
is something worth thinking about:

  - a price move >= DC_WATCH_MOVE_PCT since the last snapshot (a catalyst), AND
    at least DC_WATCH_MIN_COOLDOWN_SEC since the last full pass, OR
  - DC_WATCH_MAX_INTERVAL_SEC elapsed since the last full pass (periodic floor).

So Claude + OpenAI are spent only on catalysts or the periodic floor — the
"always-on agent" feel without burning the subscription / API credits on quiet
markets. The 3/day trade cap is still code-enforced downstream, so more passes
mean faster reaction, not more trades.

All cadence knobs are env vars (set them in .env); the defaults are conservative.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("watch_loop")

REPO = os.environ.get("REPO", "/srv/deepCommodity")                               # repo root
SYMBOLS = os.environ.get("DC_WATCH_SYMBOLS", "BTC,ETH,SOL,AVAX,LINK,ATOM,NEAR")   # cheap-poll universe
POLL_SEC = int(os.environ.get("DC_WATCH_POLL_SEC", "300"))                        # tick cadence (free poll), 5m
MOVE_PCT = float(os.environ.get("DC_WATCH_MOVE_PCT", "2.0"))                      # |move| that counts as a catalyst
MIN_COOLDOWN_SEC = int(os.environ.get("DC_WATCH_MIN_COOLDOWN_SEC", "3600"))       # floor between full passes, 1h
MAX_INTERVAL_SEC = int(os.environ.get("DC_WATCH_MAX_INTERVAL_SEC", "14400"))      # force a pass at least this often, 4h
STATE_PATH = os.path.join(REPO, "state", "watch_state.json")

_stop = False


def _handle_stop(*_a) -> None:
    global _stop
    _stop = True
    logger.info("stop signal received — exiting after this tick")


signal.signal(signal.SIGTERM, _handle_stop)
signal.signal(signal.SIGINT, _handle_stop)


def _halted() -> bool:
    """Mirror the routine halt contract: KILL_SWITCH file OR DC_HALT OR halt mode."""
    if os.path.exists(os.path.join(REPO, "KILL_SWITCH")):
        return True
    if os.environ.get("DC_HALT", "").lower() == "true":
        return True
    if os.environ.get("TRADING_MODE", "").lower() == "halt":
        return True
    return False


def _load_state() -> dict:
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except Exception:
        return {"last_pass_ts": 0.0, "prices": {}}


def _save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_PATH)


def _poll_prices() -> dict[str, float]:
    """Cheap, free price poll via tools/fetch_crypto.py (CoinGecko)."""
    try:
        out = subprocess.run(
            [sys.executable, "tools/fetch_crypto.py", "--symbols", SYMBOLS],
            cwd=REPO, capture_output=True, text=True, timeout=90,
        )
        data = json.loads(out.stdout)
        return {
            s: float(v["price_usd"])
            for s, v in data.get("symbols", {}).items()
            if v.get("price_usd")
        }
    except Exception as e:
        logger.warning("price poll failed: %s", e)
        return {}


def _max_move_pct(prev: dict, cur: dict) -> tuple[float, str]:
    best, who = 0.0, ""
    for s, p in cur.items():
        p0 = prev.get(s)
        if not p0:
            continue
        move = abs(p - p0) / p0 * 100.0
        if move > best:
            best, who = move, s
    return best, who


def _notify(msg: str) -> None:
    try:
        subprocess.run(
            [sys.executable, "tools/notify_telegram.py", "--topic", "watch",
             "--severity", "info", "--message", msg, "--quiet"],
            cwd=REPO, timeout=30,
        )
    except Exception:
        pass


def _run_decision(reason: str) -> None:
    logger.info("FIRING decision pass — %s", reason)
    _notify(f"watcher → decision ({reason})")
    try:
        subprocess.run(["bash", "deploy/run_routine.sh", "decision"], cwd=REPO, timeout=1800)
    except Exception as e:
        logger.error("decision pass error: %s", e)


def main() -> int:
    logger.info(
        "watch_loop start: symbols=%s poll=%ss move>=%.2f%% cooldown=%ss max_interval=%ss",
        SYMBOLS, POLL_SEC, MOVE_PCT, MIN_COOLDOWN_SEC, MAX_INTERVAL_SEC,
    )
    state = _load_state()
    while not _stop:
        now = time.time()
        if _halted():
            logger.info("halted (KILL_SWITCH/DC_HALT/halt-mode) — not firing")
        else:
            cur = _poll_prices()
            if cur:
                move, who = _max_move_pct(state.get("prices", {}), cur)
                since = now - float(state.get("last_pass_ts", 0.0))
                reason = ""
                if since >= MAX_INTERVAL_SEC:
                    reason = f"periodic ({int(since / 60)}m since last)"
                elif move >= MOVE_PCT and since >= MIN_COOLDOWN_SEC:
                    reason = f"catalyst: {who} {move:.1f}% move"
                if reason:
                    _run_decision(reason)
                    state["last_pass_ts"] = time.time()
                else:
                    logger.info(
                        "quiet: max move %.2f%% (%s), %dm since last pass",
                        move, who or "-", int(since / 60),
                    )
                state["prices"] = cur
                _save_state(state)
        for _ in range(POLL_SEC):  # interruptible sleep
            if _stop:
                break
            time.sleep(1)
    logger.info("watch_loop stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
