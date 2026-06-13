"""Centralized config accessors."""
from __future__ import annotations

from pathlib import Path

from deepCommodity import config


def test_trading_mode_normalizes(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "  LIVE ")
    assert config.trading_mode() == "live"
    assert config.is_live() is True
    monkeypatch.setenv("TRADING_MODE", "Halt")
    assert config.is_halt_mode() is True
    monkeypatch.delenv("TRADING_MODE", raising=False)
    assert config.trading_mode() == "paper"
    assert config.is_live() is False


def test_dc_home_precedence(monkeypatch, tmp_path):
    monkeypatch.setenv("DC_HOME", str(tmp_path))
    assert config.dc_home() == tmp_path
    assert config.dc_home(override=Path("/other")) == Path("/other")
    monkeypatch.delenv("DC_HOME", raising=False)
    assert config.dc_home() == config.REPO_ROOT


def test_repo_root_is_repo():
    assert (config.REPO_ROOT / "deepCommodity").is_dir()
    assert (config.REPO_ROOT / "tools").is_dir()


def test_authorize_live(monkeypatch):
    monkeypatch.delenv("DAILY_DECISION_AUTHORIZE_LIVE", raising=False)
    assert config.authorize_live() is False
    monkeypatch.setenv("DAILY_DECISION_AUTHORIZE_LIVE", "true")
    assert config.authorize_live() is True


def test_max_nav_usd(monkeypatch):
    monkeypatch.delenv("DC_MAX_NAV_USD", raising=False)
    assert config.max_nav_usd() == 0.0      # unset -> 0 -> caller fails closed
    monkeypatch.setenv("DC_MAX_NAV_USD", "not-a-number")
    assert config.max_nav_usd() == 0.0
    monkeypatch.setenv("DC_MAX_NAV_USD", " 500 ")
    assert config.max_nav_usd() == 500.0
