"""Forecast confidence must be clamped to [0,1]; garbage -> 0.0 (audit HIGH H1)."""
from __future__ import annotations

import importlib

forecast = importlib.import_module("tools.forecast")


def test_clamp_within_range():
    assert forecast._clamp_confidence(0.7) == 0.7


def test_clamp_over_one():
    assert forecast._clamp_confidence(5.0) == 1.0


def test_clamp_negative():
    assert forecast._clamp_confidence(-2.0) == 0.0


def test_clamp_nan_and_inf():
    assert forecast._clamp_confidence(float("nan")) == 0.0
    assert forecast._clamp_confidence(float("inf")) == 0.0


def test_clamp_garbage():
    assert forecast._clamp_confidence("not a number") == 0.0
    assert forecast._clamp_confidence(None) == 0.0


def test_input_path_outside_repo_rejected():
    import pytest
    with pytest.raises(SystemExit):
        forecast._safe_input_path("/etc/passwd")
    with pytest.raises(SystemExit):
        forecast._safe_input_path(str(forecast.ROOT.parent / ".env"))


def test_input_path_inside_repo_allowed():
    p = forecast._safe_input_path(str(forecast.ROOT / "data" / "x.json"))
    assert str(p).startswith(str(forecast.ROOT.resolve()))
