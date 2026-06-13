"""End-to-end (subprocess) exercises of place_order.py gate ORDERING.

These check the gates that fire before any broker is touched, with the right
exit codes, run from a scratch home (DC_HOME):
    1. KILL_SWITCH / halt armed    -> exit 2   (first gate)
    2. live mode not authorized    -> exit 3
The limit/oversize and happy-path behaviors are covered in test_place_order_core.py
(in-process, with a MockBroker). Every blocked order is journaled to TRADE-LOG.md.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools" / "place_order.py"


def _stage(tmp_path: Path) -> Path:
    (tmp_path / "RESEARCH-LOG.md").write_text("# RESEARCH-LOG.md\n\n---\n")
    (tmp_path / "TRADE-LOG.md").write_text("# TRADE-LOG.md\n\n---\n")
    (tmp_path / "tools").symlink_to(REPO / "tools")
    (tmp_path / "deepCommodity").symlink_to(REPO / "deepCommodity")
    return tmp_path


def _run(scratch: Path, *args, env_extra: dict | None = None):
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(REPO))
    env["DC_HOME"] = str(scratch)  # halt + trade-log anchored here, not the real repo
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=scratch, capture_output=True, text=True, env=env,
    )


BASE_ARGS = [
    "--symbol", "BTC", "--side", "buy", "--qty", "0.001",
    "--price", "60000", "--asset-class", "crypto",
    "--reason", "test", "--allow-buy",
]


def test_kill_switch_is_first_gate(tmp_path):
    s = _stage(tmp_path)
    (s / "KILL_SWITCH").write_text("test\n")
    r = _run(s, *BASE_ARGS, env_extra={"TRADING_MODE": "paper"})
    assert r.returncode == 2, r.stderr
    assert "halt" in (r.stderr + r.stdout).lower()
    log = (s / "TRADE-LOG.md").read_text()
    assert "blocked" in log.lower()


def test_live_without_confirm_blocks(tmp_path):
    s = _stage(tmp_path)
    r = _run(s, *BASE_ARGS, env_extra={
        "TRADING_MODE": "live", "DAILY_DECISION_AUTHORIZE_LIVE": "true",
    })
    assert r.returncode == 3, r.stderr
    assert "confirm-live" in (r.stderr + r.stdout)
    log = (s / "TRADE-LOG.md").read_text()
    assert "blocked" in log.lower()


def test_live_without_authorize_env_blocks(tmp_path):
    s = _stage(tmp_path)
    r = _run(s, *BASE_ARGS, env_extra={"TRADING_MODE": "live"})
    assert r.returncode == 3, r.stderr
    assert "AUTHORIZE_LIVE" in (r.stderr + r.stdout)


def test_kill_switch_precedes_live_check(tmp_path):
    """If both gates would fire, halt wins (exit 2, not 3)."""
    s = _stage(tmp_path)
    (s / "KILL_SWITCH").write_text("priority test\n")
    r = _run(s, *BASE_ARGS, env_extra={"TRADING_MODE": "live"})
    assert r.returncode == 2, r.stderr


def test_dc_halt_env_blocks(tmp_path):
    s = _stage(tmp_path)
    r = _run(s, *BASE_ARGS, env_extra={"TRADING_MODE": "paper", "DC_HALT": "true"})
    assert r.returncode == 2, r.stderr
