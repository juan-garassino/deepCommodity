"""preflight() is the single chokepoint to broker.submit — fail-closed everywhere.

Locks: halt blocks (env + file + unconfirmable), portfolio-unavailable blocks (B3),
and all enhanced limits are enforced through it.
"""
from __future__ import annotations

import pytest

from deepCommodity.execution.portfolio import MockPortfolioProvider, PortfolioUnavailable
from deepCommodity.guardrails.kill_switch import halt_state
from deepCommodity.guardrails.limits import OrderProposal, PortfolioSnapshot
from deepCommodity.guardrails.preflight import Decision, preflight


def _provider(nav=10_000.0, cash=10_000.0, positions=None, sector_notional=None,
              new_positions_today=None):
    snap = PortfolioSnapshot(
        nav_usd=nav, cash_usd=cash, positions=positions or {},
        sector_notional=sector_notional or {},
        new_positions_today=new_positions_today or {},
    )
    return MockPortfolioProvider(snapshot=snap)


def _buy(notional=100.0, symbol="MSFT", bucket="anchor"):
    return OrderProposal(symbol=symbol, side="buy", qty=1, notional_usd=notional, bucket=bucket)


# ---- halt_state --------------------------------------------------------------

def test_halt_state_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DC_HALT", "true")
    halted, confirmed, _ = halt_state(root=tmp_path)
    assert halted and confirmed


def test_halt_state_trading_mode_halt(monkeypatch, tmp_path):
    monkeypatch.delenv("DC_HALT", raising=False)
    monkeypatch.setenv("TRADING_MODE", "halt")
    halted, confirmed, _ = halt_state(root=tmp_path)
    assert halted and confirmed


def test_halt_state_file(monkeypatch, tmp_path):
    monkeypatch.delenv("DC_HALT", raising=False)
    monkeypatch.setenv("TRADING_MODE", "paper")
    (tmp_path / "KILL_SWITCH").write_text("x")
    halted, confirmed, _ = halt_state(root=tmp_path)
    assert halted and confirmed


def test_halt_state_clear(monkeypatch, tmp_path):
    monkeypatch.delenv("DC_HALT", raising=False)
    monkeypatch.setenv("TRADING_MODE", "paper")
    halted, confirmed, _ = halt_state(root=tmp_path)
    assert not halted and confirmed


# ---- preflight ---------------------------------------------------------------

def test_preflight_blocks_when_halted(monkeypatch, tmp_path):
    monkeypatch.setenv("DC_HALT", "1")
    d = preflight(_buy(), _provider(), root=tmp_path)
    assert isinstance(d, Decision)
    assert not d.allow and d.code == "halt"


def test_preflight_blocks_when_portfolio_unavailable(monkeypatch, tmp_path):
    monkeypatch.delenv("DC_HALT", raising=False)
    monkeypatch.setenv("TRADING_MODE", "paper")
    prov = MockPortfolioProvider(raises=PortfolioUnavailable("api down"))
    d = preflight(_buy(), prov, root=tmp_path)
    assert not d.allow and d.code == "unavailable"


def test_preflight_allows_clean_buy(monkeypatch, tmp_path):
    monkeypatch.delenv("DC_HALT", raising=False)
    monkeypatch.setenv("TRADING_MODE", "paper")
    d = preflight(_buy(notional=100.0), _provider(), root=tmp_path)
    assert d.allow and d.code == "ok"


def test_preflight_enforces_limits(monkeypatch, tmp_path):
    monkeypatch.delenv("DC_HALT", raising=False)
    monkeypatch.setenv("TRADING_MODE", "paper")
    d = preflight(_buy(notional=600.0), _provider(), root=tmp_path)  # 6% > 5%
    assert not d.allow and d.code == "blocked"


def test_preflight_blocks_nan(monkeypatch, tmp_path):
    monkeypatch.delenv("DC_HALT", raising=False)
    monkeypatch.setenv("TRADING_MODE", "paper")
    bad = OrderProposal(symbol="BTC", side="buy", qty=1, notional_usd=float("nan"), bucket="anchor")
    d = preflight(bad, _provider(), root=tmp_path)
    assert not d.allow
