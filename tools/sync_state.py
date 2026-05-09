#!/usr/bin/env python
"""Bootstrap state at the start of a managed (cloud-sandbox) routine.

What it does:
  1. Source a local .env if one exists (VPS deployment).
     On Anthropic's cloud routines, env vars come pre-injected from the
     environment configured at claude.ai/code/routines, so no .env file is
     present and this step is a no-op.
  2. Optionally apply env from a JSON file the agent fetched (e.g. via Drive
     connector). Mostly an escape hatch for non-cloud deployments.
  3. Fetch the claude/logs branch so the agent can read the prior run's
     RESEARCH-LOG / TRADE-LOG state.
  4. Verify KILL_SWITCH visibility (file in the working tree).
  5. Advisory check on required env keys; warns but does not abort.

Safe to call from every routine on every deployment.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# ---- env -------------------------------------------------------------------

def load_local_env(path: Path) -> int:
    """Source a key=value .env file into os.environ. Returns count of vars set."""
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip().strip('"').strip("'")
        n += 1
    return n


def load_env_json(payload: dict) -> int:
    """Decode {key: value} JSON and inject into os.environ."""
    n = 0
    for k, v in payload.items():
        if v is None or v == "":
            continue
        os.environ[str(k)] = str(v)
        n += 1
    return n


# ---- git -------------------------------------------------------------------

def git_pull() -> bool:
    try:
        r = subprocess.run(["git", "pull", "--ff-only", "--no-edit"],
                           cwd=ROOT, capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            print(f"  git pull: {r.stdout.strip()[:120]}")
            return True
        print(f"  git pull: {r.stderr.strip()[:200]}", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"  git pull failed: {e}", file=sys.stderr)
    return False


def fetch_log_branch(branch: str = "claude/logs") -> bool:
    """Pull the latest contents of the log branch into the working tree
    without switching off the routine's branch."""
    try:
        fetch = subprocess.run(["git", "fetch", "origin", branch, "--depth=1"],
                               cwd=ROOT, capture_output=True, text=True, timeout=30)
        if fetch.returncode != 0:
            print(f"  log-branch '{branch}' not fetched (likely first run): "
                  f"{fetch.stderr.strip()[:120]}")
            return False
        n = 0
        for f in ("RESEARCH-LOG.md", "TRADE-LOG.md", "WEEKLY-REVIEW.md", "KILL_SWITCH"):
            r = subprocess.run(["git", "checkout", f"origin/{branch}", "--", f],
                               cwd=ROOT, capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                n += 1
        print(f"  fetched {n} files from {branch}")
        return n > 0
    except Exception as e:  # noqa: BLE001
        print(f"  log-branch fetch failed: {e}", file=sys.stderr)
        return False


# ---- main ------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--env-json",
                   help="optional JSON file with extra env vars. Cloud routines "
                        "get env from the routine environment; this is for "
                        "non-cloud deployments only.")
    p.add_argument("--skip-pull", action="store_true",
                   help="skip git pull (default true on managed routines, where "
                        "the sandbox already cloned fresh)")
    p.add_argument("--log-branch", default="claude/logs",
                   help="branch the routines push log updates to. "
                        "Default: claude/logs.")
    p.add_argument("--models-dir",
                   help="local destination for synced model checkpoints")
    args = p.parse_args()

    print("sync_state: starting")

    # 1. env from JSON (escape hatch — not used on managed routines)
    if args.env_json:
        ej = Path(args.env_json)
        if ej.exists():
            n = load_env_json(json.loads(ej.read_text()))
            print(f"  loaded {n} env vars from {ej}")
        else:
            print(f"  --env-json={ej} not found", file=sys.stderr)

    # 2. local .env (VPS path)
    n = load_local_env(ROOT / ".env")
    if n:
        print(f"  loaded {n} env vars from .env")

    # 3. fetch log branch contents into the working tree
    fetch_log_branch(args.log_branch)

    # 4. git pull main (skipped on managed routines — sandbox is fresh)
    if not args.skip_pull:
        git_pull()

    # 5. models destination
    if args.models_dir:
        Path(args.models_dir).mkdir(parents=True, exist_ok=True)
        print(f"  models dir ready at {args.models_dir}")

    # 6. KILL_SWITCH visibility
    if (ROOT / "KILL_SWITCH").exists():
        print("  KILL_SWITCH present — order placement will be blocked")
    else:
        print("  KILL_SWITCH absent")

    # 7. advisory env check
    required = {
        "TELEGRAM_BOT_TOKEN": "Telegram alerts disabled",
        "BINANCE_API_KEY": "crypto trading disabled",
        "ALPACA_API_KEY": "equity trading disabled",
        "OPENAI_API_KEY": "news fetch disabled (or set PERPLEXITY_API_KEY)",
    }
    for var, fallback in required.items():
        if not os.getenv(var):
            print(f"  warn: {var} missing — {fallback}")

    print("sync_state: done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
