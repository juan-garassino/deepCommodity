"""BrokerPortfolioProvider assembles a real PortfolioSnapshot, fail-closed.

Locks audit fix B3 (no fabricated fallback) and B5 (USD-correct valuation feeds
sector/leverage/cash gates) plus per-bucket new-position counting from real fills.
"""
from __future__ import annotations

import pytest

from datetime import datetime, timezone

from deepCommodity.execution.portfolio import (
    BrokerPortfolioProvider,
    MockPortfolioProvider,
    PortfolioUnavailable,
    count_new_positions_today,
)
from deepCommodity.guardrails.limits import PortfolioSnapshot
from deepCommodity.universe import Universe


class _FakeBroker:
    name = "fake"

    def __init__(self, nav, positions, cash, fail=False):
        self._nav, self._positions, self._cash = nav, positions, cash
        self._fail = fail

    def account_state(self):
        if self._fail:
            raise RuntimeError("api down")
        return self._nav, self._positions, self._cash


U = Universe.load()


def test_snapshot_passes_through_nav_cash_positions():
    b = _FakeBroker(nav=10_000.0, positions={"BTC": 3000.0}, cash=7000.0)
    snap = BrokerPortfolioProvider(b, U).snapshot()
    assert isinstance(snap, PortfolioSnapshot)
    assert snap.nav_usd == 10_000.0
    assert snap.cash_usd == 7000.0
    assert snap.positions == {"BTC": 3000.0}
    assert snap.source == "fake"


def test_snapshot_aggregates_sector_notional():
    # CCJ -> nuclear theme; SMR -> nuclear; AAPL -> anchor (no sector)
    b = _FakeBroker(nav=10_000.0, cash=5000.0,
                    positions={"CCJ": 1000.0, "SMR": 500.0, "AAPL": 2000.0})
    snap = BrokerPortfolioProvider(b, U).snapshot()
    assert snap.sector_notional.get("nuclear") == 1500.0
    assert "anchor" not in snap.sector_notional  # anchors are sector-exempt


def test_count_new_positions_today_from_trade_log(tmp_path):
    today = "2026-06-13"
    log = tmp_path / "TRADE-LOG.md"
    log.write_text(
        f"# TRADE LOG\n"
        f"## {today} 10:00 UTC — FILLED BUY 1 AAPL\n- symbol: AAPL\n- side: buy\n- status: filled\n\n"
        f"## {today} 11:00 UTC — FILLED BUY 1 CCJ\n- symbol: CCJ\n- side: buy\n- status: filled\n\n"
        f"## 2000-01-01 09:00 UTC — FILLED BUY 1 SOL\n- symbol: SOL\n- side: buy\n- status: filled\n\n"
        f"## {today} 12:00 UTC — BLOCKED BUY 1 MSFT\n- symbol: MSFT\n- side: buy\n- status: blocked\n\n"
        f"## {today} 13:00 UTC — FILLED SELL 1 BTC\n- symbol: BTC\n- side: sell\n- status: filled\n\n"
        f"## {today} 14:00 UTC — PLACED BUY 1 GOOGL\n- symbol: GOOGL\n- side: buy\n- status: placed\n"
    )
    counts = count_new_positions_today(log, U, today)
    assert counts.get("anchor") == 2   # AAPL (filled) + GOOGL (placed) both count
    assert counts.get("theme") == 1    # CCJ filled buy today
    assert sum(counts.values()) == 3   # SOL old date, MSFT blocked, BTC sell -> excluded


def test_snapshot_reads_daily_count_from_trade_log(tmp_path):
    log = tmp_path / "TRADE-LOG.md"
    log.write_text(
        "## 2026-06-13 10:00 UTC — FILLED BUY 1 AAPL\n- symbol: AAPL\n- side: buy\n- status: filled\n"
    )
    b = _FakeBroker(nav=10_000.0, cash=5000.0, positions={})
    snap = BrokerPortfolioProvider(
        b, U, now=datetime(2026, 6, 13, tzinfo=timezone.utc), trade_log_path=log
    ).snapshot()
    assert snap.new_positions_today.get("anchor") == 1


def test_count_missing_log_is_empty(tmp_path):
    assert count_new_positions_today(tmp_path / "nope.md", U, "2026-06-13") == {}


def test_snapshot_fails_closed_on_broker_error():
    b = _FakeBroker(nav=0, positions={}, cash=0, fail=True)
    with pytest.raises(PortfolioUnavailable):
        BrokerPortfolioProvider(b, U).snapshot()


def test_mock_provider_returns_supplied_snapshot():
    snap = PortfolioSnapshot(nav_usd=1.0, cash_usd=1.0, positions={}, sector_notional={})
    assert MockPortfolioProvider(snapshot=snap).snapshot() is snap


def test_mock_provider_can_raise_unavailable():
    with pytest.raises(PortfolioUnavailable):
        MockPortfolioProvider(raises=PortfolioUnavailable("x")).snapshot()
