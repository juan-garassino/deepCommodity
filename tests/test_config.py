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
