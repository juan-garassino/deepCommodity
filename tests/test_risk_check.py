"""risk_check.evaluate is the standalone pre-trade gate (CLI exit contract).

    exit 0 = OK | 1 = blocked/unavailable | 2 = halt
Previously untested standalone (audit gap H1/test).
"""
from __future__ import annotations

import importlib

risk_check = importlib.import_module("tools.risk_check")

from tests._mocks import provider_for, MockPortfolioProvider, PortfolioUnavailable  # noqa: E402


def _eval(monkeypatch, tmp_path, *, provider, qty=1.0, price=100.0, mode="paper", halt=False):
    monkeypatch.setenv("TRADING_MODE", mode)
    monkeypatch.delenv("DC_HALT", raising=False)
    if halt:
        (tmp_path / "KILL_SWITCH").write_text("x")
    return risk_check.evaluate(
        symbol="AAPL", side="buy", qty=qty, price=price, asset_class="equity",
        provider=provider, home=tmp_path,
    )


def test_clean_buy_exit_0(monkeypatch, tmp_path):
    code, reason = _eval(monkeypatch, tmp_path, provider=provider_for())
    assert code == 0


def test_oversize_exit_1(monkeypatch, tmp_path):
    code, reason = _eval(monkeypatch, tmp_path, provider=provider_for(), qty=600, price=100)
    assert code == 1
    assert "BLOCKED" in reason


def test_halt_exit_2(monkeypatch, tmp_path):
    code, reason = _eval(monkeypatch, tmp_path, provider=provider_for(), halt=True)
    assert code == 2


def test_portfolio_unavailable_exit_1(monkeypatch, tmp_path):
    prov = MockPortfolioProvider(raises=PortfolioUnavailable("api down"))
    code, reason = _eval(monkeypatch, tmp_path, provider=prov)
    assert code == 1
    assert "unavailable" in reason.lower()
