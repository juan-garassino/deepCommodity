"""End-to-end exercises of the three place_order.py hard gates.

These tests do NOT hit a real broker. They run the CLI and check that the
gates fire in the right order with the right exit codes:
    1. KILL_SWITCH armed       -> exit 2
    2. live mode w/o confirm   -> exit 3
    3. risk_check fails        -> exit 1
And that every blocked order is journaled to TRADE-LOG.md.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools" / "place_order.py"


def _stage(tmp_path: Path) -> Path:
    """Make a minimal trade-log + journal copy at tmp_path so we can run the CLI cwd'd there."""
    (tmp_path / "RESEARCH-LOG.md").write_text("# RESEARCH-LOG.md\n\n---\n")
    (tmp_path / "TRADE-LOG.md").write_text("# TRADE-LOG.md\n\n---\n")
    # Symlink the tools/ dir so place_order.py can find journal.py + the package
    (tmp_path / "tools").symlink_to(REPO / "tools")
    (tmp_path / "deepCommodity").symlink_to(REPO / "deepCommodity")
    return tmp_path


def _run(scratch: Path, *args, env_extra: dict | None = None):
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(REPO))
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=scratch, capture_output=True, text=True, env=env,
    )


BASE_ARGS = [
    "--symbol", "BTC", "--side", "buy", "--qty", "0.001",
    "--price", "60000", "--asset-class", "crypto",
    "--reason", "test",
]


def test_kill_switch_is_first_gate(tmp_path):
    s = _stage(tmp_path)
    (s / "KILL_SWITCH").write_text("test\n")
    r = _run(s, *BASE_ARGS, env_extra={"TRADING_MODE": "paper"})
    assert r.returncode == 2, r.stderr
    assert "KILL_SWITCH" in (r.stderr + r.stdout)
    log = (s / "TRADE-LOG.md").read_text()
    assert "blocked" in log.lower() and "KILL_SWITCH" in log


def test_live_without_confirm_blocks(tmp_path):
    s = _stage(tmp_path)
    r = _run(s, *BASE_ARGS, env_extra={"TRADING_MODE": "live"})
    assert r.returncode == 3, r.stderr
    assert "confirm-live" in (r.stderr + r.stdout)
    log = (s / "TRADE-LOG.md").read_text()
    assert "blocked" in log.lower()


def test_risk_check_blocks_oversize(tmp_path):
    s = _stage(tmp_path)
    big = ["--symbol", "BTC", "--side", "buy", "--qty", "999",
           "--price", "60000", "--asset-class", "crypto", "--reason", "oversize"]
    r = _run(s, *big, env_extra={"TRADING_MODE": "paper"})
    assert r.returncode == 1, r.stderr
    assert "BLOCKED" in (r.stderr + r.stdout)
    log = (s / "TRADE-LOG.md").read_text()
    assert "blocked" in log.lower()


def test_kill_switch_precedes_live_check(tmp_path):
    """If both gates would fire, kill-switch wins (exit 2, not 3)."""
    s = _stage(tmp_path)
    (s / "KILL_SWITCH").write_text("priority test\n")
    r = _run(s, *BASE_ARGS, env_extra={"TRADING_MODE": "live"})
    assert r.returncode == 2, r.stderr


def test_kill_switch_precedes_risk_check(tmp_path):
    s = _stage(tmp_path)
    (s / "KILL_SWITCH").write_text("priority test\n")
    big = ["--symbol", "BTC", "--side", "buy", "--qty", "999",
           "--price", "60000", "--asset-class", "crypto", "--reason", "oversize"]
    r = _run(s, *big, env_extra={"TRADING_MODE": "paper"})
    assert r.returncode == 2, r.stderr
