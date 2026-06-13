"""In-process tests of place_order.execute — the full gated submit path.

Uses MockBroker + MockPortfolioProvider so we can drive the happy path, broker
rejection, idempotency, the 3-gate live authorization, and the live NAV ceiling
without a real broker. Exit-code contract:
    0 ok | 1 blocked/unavailable | 2 halt | 3 live-not-authorized | 4 broker reject
    5 buy without --allow-buy
"""
from __future__ import annotations

import importlib

import pytest

place_order = importlib.import_module("tools.place_order")

from tests._mocks import MockBroker, provider_for  # noqa: E402


def _stage_home(tmp_path):
    (tmp_path / "TRADE-LOG.md").write_text("# TRADE-LOG.md\n")
    (tmp_path / "RESEARCH-LOG.md").write_text("# RESEARCH-LOG.md\n")
    return tmp_path


def _run(tmp_path, monkeypatch, *, side="buy", qty=1.0, allow_buy=True,
         confirm_live=False, provider=None, broker=None, mode="paper",
         asset_class="equity", symbol="AAPL", **env):
    home = _stage_home(tmp_path)
    monkeypatch.chdir(home)
    monkeypatch.setenv("TRADING_MODE", mode)
    monkeypatch.delenv("DC_HALT", raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    broker = broker or MockBroker()
    provider = provider or provider_for()
    return place_order.execute(
        symbol=symbol, side=side, qty=qty, asset_class=asset_class,
        reason="test thesis sufficiently long for any bucket gate requirement here",
        allow_buy=allow_buy, confirm_live=confirm_live,
        provider=provider, broker=broker, home=home,
    ), broker, home


def test_happy_path_submits_once_and_journals_filled(tmp_path, monkeypatch):
    code, broker, home = _run(tmp_path, monkeypatch)
    assert code == 0
    assert len(broker.calls) == 1
    log = (home / "TRADE-LOG.md").read_text().lower()
    assert "filled" in log


def test_broker_rejection_returns_4(tmp_path, monkeypatch):
    broker = MockBroker(ok=False, error="insufficient balance")
    code, broker, home = _run(tmp_path, monkeypatch, broker=broker)
    assert code == 4
    assert "rejected" in (home / "TRADE-LOG.md").read_text().lower()


def test_oversize_blocked_and_no_submit(tmp_path, monkeypatch):
    # ref_price 100 * qty 600 = 60_000 notional on 10k nav -> way over 5%
    broker = MockBroker(ref_price=100.0)
    code, broker, home = _run(tmp_path, monkeypatch, qty=600, broker=broker)
    assert code == 1
    assert broker.calls == []


def test_halt_blocks_with_2(tmp_path, monkeypatch):
    home = _stage_home(tmp_path)
    (home / "KILL_SWITCH").write_text("halt")
    monkeypatch.chdir(home)
    monkeypatch.setenv("TRADING_MODE", "paper")
    broker = MockBroker()
    code = place_order.execute(
        symbol="AAPL", side="buy", qty=1.0, asset_class="equity", reason="x",
        allow_buy=True, provider=provider_for(), broker=broker, home=home,
    )
    assert code == 2
    assert broker.calls == []


def test_buy_without_allow_buy_blocked_with_5(tmp_path, monkeypatch):
    code, broker, home = _run(tmp_path, monkeypatch, allow_buy=False)
    assert code == 5
    assert broker.calls == []


def test_sell_does_not_require_allow_buy(tmp_path, monkeypatch):
    code, broker, home = _run(tmp_path, monkeypatch, side="sell", allow_buy=False)
    assert code == 0
    assert len(broker.calls) == 1


def test_live_without_authorize_env_blocked_with_3(tmp_path, monkeypatch):
    monkeypatch.delenv("DAILY_DECISION_AUTHORIZE_LIVE", raising=False)
    code, broker, home = _run(tmp_path, monkeypatch, mode="live", confirm_live=True)
    assert code == 3
    assert broker.calls == []


def test_live_without_confirm_flag_blocked_with_3(tmp_path, monkeypatch):
    code, broker, home = _run(tmp_path, monkeypatch, mode="live", confirm_live=False,
                              DAILY_DECISION_AUTHORIZE_LIVE="true",
                              ALPACA_PAPER="false")
    assert code == 3
    assert broker.calls == []


def test_live_nav_ceiling_blocks(tmp_path, monkeypatch):
    # all 3 live gates pass, but NAV exceeds the configured ceiling
    prov = provider_for(nav=10_000.0)
    code, broker, home = _run(
        tmp_path, monkeypatch, mode="live", confirm_live=True, provider=prov,
        DAILY_DECISION_AUTHORIZE_LIVE="true", ALPACA_PAPER="false",
        DC_MAX_NAV_USD="5000",
    )
    assert code == 3
    assert broker.calls == []


def test_live_requires_positive_ceiling(tmp_path, monkeypatch):
    # all 3 live gates pass but DC_MAX_NAV_USD is unset -> fail closed (no unbounded live)
    monkeypatch.delenv("DC_MAX_NAV_USD", raising=False)
    code, broker, home = _run(
        tmp_path, monkeypatch, mode="live", confirm_live=True,
        DAILY_DECISION_AUTHORIZE_LIVE="true", ALPACA_PAPER="false",
    )
    assert code == 3
    assert broker.calls == []


def test_buy_without_broker_quote_blocked(tmp_path, monkeypatch):
    broker = MockBroker(ref_raise=True)  # broker can't quote -> must not fall back to --price
    code, broker, home = _run(tmp_path, monkeypatch, broker=broker)
    assert code == 1
    assert broker.calls == []


def test_lowercase_symbol_cannot_bypass_pyramiding(tmp_path, monkeypatch):
    # already hold 400 of BTC; a lowercase "btc" buy of 200 -> combined 6% > 5% must block
    broker = MockBroker(ref_price=100.0)  # qty 2 * 100 = 200 notional
    prov = provider_for(positions={"BTC": 400.0})
    code, broker, home = _run(tmp_path, monkeypatch, symbol="btc", asset_class="crypto",
                              qty=2, broker=broker, provider=prov)
    assert code == 1
    assert broker.calls == []


def test_idempotency_key_is_deterministic(tmp_path, monkeypatch):
    b1 = MockBroker()
    _run(tmp_path, monkeypatch, broker=b1)
    b2 = MockBroker()
    _run(tmp_path, monkeypatch, broker=b2)
    assert b1.calls[0].client_order_id
    assert b1.calls[0].client_order_id == b2.calls[0].client_order_id
