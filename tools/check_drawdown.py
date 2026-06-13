#!/usr/bin/env python
"""Drawdown circuit breaker (audit fix B4). Run by the position-mgmt routine.

Fetches total NAV across venues, compares it to the persisted day/week baseline,
and ARMS the KILL_SWITCH on a >=4% daily or >=8% weekly drawdown. Fail-closed: if
NAV cannot be fetched, arm the switch rather than trade blind. Never opens orders.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.guardrails.circuit_breaker import arm_kill_switch, evaluate_drawdown  # noqa: E402


def _home(home: Path | None = None) -> Path:
    return Path(home or os.getenv("DC_HOME") or ROOT)


def _total_nav() -> float:
    """Sum NAV across crypto + equity venues. Raises if any required venue fails."""
    from deepCommodity.execution.portfolio import build_snapshot

    total = 0.0
    for asset_class in ("crypto", "equity"):
        total += build_snapshot(asset_class).nav_usd
    return total


def run(nav_fetcher, baseline_path: Path, root: Path, now: datetime | None = None) -> bool:
    """Evaluate drawdown and arm the kill switch if breached or NAV unavailable.

    Returns True if the kill switch ended up armed by this run.
    """
    now = now or datetime.now(timezone.utc)
    baseline_path = Path(baseline_path)
    try:
        nav = float(nav_fetcher())
    except Exception as e:  # noqa: BLE001 — fail closed
        arm_kill_switch(f"drawdown check could not read NAV: {e}", root=root)
        return True

    try:
        baseline = json.loads(baseline_path.read_text())
    except (OSError, ValueError):
        baseline = {}

    new_baseline, should_arm, reason = evaluate_drawdown(nav, baseline, now)
    try:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(json.dumps(new_baseline, indent=2))
    except OSError:
        pass

    if should_arm:
        arm_kill_switch(f"drawdown breaker: {reason}", root=root)
        return True
    return False


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", default=str(_home() / "state" / "nav_baseline.json"))
    args = p.parse_args()
    armed = run(_total_nav, Path(args.baseline), root=_home())
    print(json.dumps({"armed": armed}, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
