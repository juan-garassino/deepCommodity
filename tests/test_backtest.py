"""Backtest engine sanity tests with synthetic bars."""
from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from deepCommodity.backtest import BacktestConfig, run_backtest
from deepCommodity.backtest.engine import Bar, Forecast, PaperBook
from deepCommodity.backtest.forecasters import rule_based


def _ramp(symbol: str, n: int = 400, slope: float = 0.001, start: float = 100.0):
    base = datetime(2025, 1, 1)
    return [Bar(ts=base + timedelta(hours=i), close=start * (1 + slope * i))
            for i in range(n)]


def _flat(symbol: str, n: int = 400, price: float = 100.0):
    base = datetime(2025, 1, 1)
    return [Bar(ts=base + timedelta(hours=i), close=price) for i in range(n)]


def _crash(symbol: str, n: int = 400, start: float = 100.0):
    base = datetime(2025, 1, 1)
    return [Bar(ts=base + timedelta(hours=i),
                close=max(1.0, start - 0.2 * i)) for i in range(n)]


def test_backtest_profits_on_steady_uptrend():
    bars = {"X": _ramp("X")}
    cfg = BacktestConfig(starting_nav=10_000, warmup_bars=168, rebalance_every=24)
    res = run_backtest(bars, rule_based, cfg)
    assert res.final_nav > cfg.starting_nav
    assert res.return_pct > 0
    assert res.n_trades >= 1


def test_backtest_no_trades_on_flat_market():
    bars = {"X": _flat("X")}
    cfg = BacktestConfig(starting_nav=10_000, warmup_bars=168, rebalance_every=24)
    res = run_backtest(bars, rule_based, cfg)
    # rule-based forecaster goes flat with confidence 0.4 < 0.6 threshold
    assert res.n_trades == 0
    assert math.isclose(res.final_nav, cfg.starting_nav, rel_tol=1e-9)


def test_backtest_handles_crash_without_blowing_up():
    bars = {"X": _crash("X")}
    cfg = BacktestConfig(starting_nav=10_000, warmup_bars=168, rebalance_every=24)
    res = run_backtest(bars, rule_based, cfg)
    # NAV may dip but we never go negative — the engine must be solvent.
    assert res.final_nav > 0


def test_backtest_uses_risk_check():
    """If risk_check is enforced, the per-position cap (5% of NAV) limits exposure."""
    bars = {"X": _ramp("X")}
    cfg = BacktestConfig(starting_nav=10_000, position_pct=0.50, warmup_bars=168,
                         rebalance_every=24, enforce_risk_check=True)
    res = run_backtest(bars, rule_based, cfg)
    # All buys should be blocked because notional 50% > hard cap 5%.
    assert res.n_trades == 0
    assert res.n_blocked > 0


def test_backtest_without_risk_check_allows_oversize():
    bars = {"X": _ramp("X")}
    cfg = BacktestConfig(starting_nav=10_000, position_pct=0.50, warmup_bars=168,
                         rebalance_every=24, enforce_risk_check=False)
    res = run_backtest(bars, rule_based, cfg)
    assert res.n_trades >= 1


def test_paperbook_rejects_oversold():
    cfg = BacktestConfig()
    book = PaperBook(cfg)
    ts = datetime(2025, 1, 1)
    ok = book.submit(ts, "X", "sell", 10, 100.0)
    assert not ok
    assert book.blocked == 1


def test_paperbook_average_entry_correct_on_adds():
    cfg = BacktestConfig(transaction_cost_bps=0, slippage_bps=0)
    book = PaperBook(cfg)
    ts = datetime(2025, 1, 1)
    book.submit(ts, "X", "buy", 1, 100.0)
    book.submit(ts, "X", "buy", 3, 200.0)
    qty, avg = book.positions["X"]
    assert qty == 4
    assert math.isclose(avg, (1*100 + 3*200) / 4)


def test_warmup_too_short_raises():
    bars = {"X": _ramp("X", n=50)}
    cfg = BacktestConfig(warmup_bars=100)
    with pytest.raises(ValueError):
        run_backtest(bars, rule_based, cfg)


def test_custom_forecaster_signature_works():
    """Anything matching (window) -> [Forecast] is a valid forecaster."""
    def always_long(window):
        return [Forecast(s, "long", 0.99) for s in window]
    bars = {"X": _ramp("X")}
    cfg = BacktestConfig(starting_nav=10_000, warmup_bars=168, rebalance_every=48,
                         enforce_risk_check=False)
    res = run_backtest(bars, always_long, cfg)
    assert res.n_trades >= 1
