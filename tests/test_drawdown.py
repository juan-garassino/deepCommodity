"""Drawdown breaker wiring (audit fix B4): -4% daily / -8% weekly auto-arms KILL_SWITCH.

Previously daily_pnl_breach/weekly_pnl_breach existed but nothing called them.
"""
from __future__ import annotations

import importlib
from datetime import datetime, timezone

from deepCommodity.guardrails.circuit_breaker import evaluate_drawdown
from deepCommodity.guardrails.kill_switch import is_armed

check_drawdown = importlib.import_module("tools.check_drawdown")

NOW = datetime(2026, 6, 13, 14, 0, tzinfo=timezone.utc)


def test_new_day_sets_baseline_no_arm():
    new, armed, _ = evaluate_drawdown(10_000.0, {}, NOW)
    assert not armed
    assert new["daily_nav"] == 10_000.0
    assert new["daily_date"] == "2026-06-13"


def test_daily_drawdown_arms():
    base = {"daily_date": "2026-06-13", "daily_nav": 10_000.0,
            "weekly_week": "2026-W24", "weekly_nav": 10_000.0}
    _, armed, reason = evaluate_drawdown(9_500.0, base, NOW)  # -5%
    assert armed
    assert "daily" in reason.lower()


def test_daily_minor_drop_no_arm():
    base = {"daily_date": "2026-06-13", "daily_nav": 10_000.0,
            "weekly_week": "2026-W24", "weekly_nav": 10_000.0}
    _, armed, _ = evaluate_drawdown(9_700.0, base, NOW)  # -3%
    assert not armed


def test_weekly_drawdown_arms():
    base = {"daily_date": "2026-06-13", "daily_nav": 10_000.0,
            "weekly_week": "2026-W24", "weekly_nav": 10_000.0}
    _, armed, reason = evaluate_drawdown(9_100.0, base, NOW)  # -9% weekly (and -9% daily)
    assert armed


def test_tool_arms_kill_switch_on_breach(tmp_path):
    baseline = tmp_path / "nav_baseline.json"
    baseline.write_text(
        '{"daily_date":"2026-06-13","daily_nav":10000.0,'
        '"weekly_week":"2026-W24","weekly_nav":10000.0}'
    )
    armed = check_drawdown.run(
        nav_fetcher=lambda: 9_400.0, baseline_path=baseline, root=tmp_path, now=NOW
    )
    assert armed is True
    assert is_armed(root=tmp_path)


def test_tool_fails_closed_when_nav_unavailable(tmp_path):
    def boom():
        raise RuntimeError("broker down")
    armed = check_drawdown.run(
        nav_fetcher=boom, baseline_path=tmp_path / "nav_baseline.json",
        root=tmp_path, now=NOW,
    )
    assert armed is True
    assert is_armed(root=tmp_path)
