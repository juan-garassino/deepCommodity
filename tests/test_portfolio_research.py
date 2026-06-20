"""Portfolio-research sleeves, risk overlay, and backtester invariants.

Motivating sources:
  deepCommodity/portfolio/{sleeves,risk,backtest,portfolios}.py
Synthetic inputs — no network.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.portfolio import backtest, risk, sleeves, signals  # noqa: E402
from deepCommodity.portfolio.portfolios import Costs, PortfolioCfg, build_weights, load_portfolios  # noqa: E402


def _prices(n=300, k=8):
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    rng = np.random.default_rng(1)
    steps = rng.standard_normal((n, k)) * 0.03
    return pd.DataFrame(100 * np.exp(np.cumsum(steps, axis=0)), index=idx,
                        columns=[f"A{i}" for i in range(k)])


def test_xs_weights_dollar_neutral():
    w = sleeves.xs_weights(signals.xs_score(_prices()))
    active = w[(w != 0).any(axis=1)]
    assert np.allclose(active.sum(axis=1), 0.0, atol=1e-9)          # net ~ 0
    assert np.allclose(active.abs().sum(axis=1), 1.0, atol=1e-9)    # gross ~ 1


def test_carry_weights_nonneg_and_sum_one():
    funding = pd.DataFrame(np.random.default_rng(2).standard_normal((100, 5)) * 1e-3,
                           columns=[f"A{i}" for i in range(5)])
    w = sleeves.carry_weights(signals.carry_score(funding))
    active = w[(w != 0).any(axis=1)]
    assert (active.values >= 0).all()
    assert np.allclose(active.sum(axis=1), 1.0, atol=1e-9)


def test_dd_ladder_ramp():
    assert risk.dd_multiplier(0.0, -0.04, -0.08) == 1.0
    assert risk.dd_multiplier(-0.08, -0.04, -0.08) == 0.0
    assert risk.dd_multiplier(-0.20, -0.04, -0.08) == 0.0
    assert 0.0 < risk.dd_multiplier(-0.06, -0.04, -0.08) < 1.0


def test_vol_scale_and_gross_cap():
    quiet = np.full(30, 0.001)
    hot = np.random.default_rng(3).standard_normal(30) * 0.05
    assert risk.vol_scale(quiet, 0.12, 3.0) > risk.vol_scale(hot, 0.12, 3.0)
    p, c = risk.cap_gross(np.array([0.6, -0.6, 0.4]), np.array([0.5]), 1.0)
    assert abs(np.abs(p).sum() + np.abs(c).sum() - 1.0) < 1e-9


def test_build_weights_long_only_clips():
    cfg = PortfolioCfg("x", {"xs": 1.0}, 1.0, 0.2, 0.15, -0.04, -0.08, long_only=True)
    sc = signals.xs_score(_prices())
    xs_w = sleeves.xs_weights(sc)
    dir_w = pd.DataFrame(0.0, index=xs_w.index, columns=xs_w.columns)
    pw, _ = build_weights(cfg, xs_w, sleeves.carry_weights(sc.clip(lower=0)), dir_w)
    assert (pw.values >= 0).all()                                  # no shorts


def test_backtest_runs_and_metrics_finite():
    prices = _prices()
    funding = pd.DataFrame(0.0001, index=prices.index, columns=prices.columns)
    cfg = PortfolioCfg("t", {"xs": 1.0}, 2.0, 0.2, 0.12, -0.06, -0.12)
    pw = sleeves.xs_weights(signals.xs_score(prices))
    cw = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    res = backtest.run(pw, cw, prices.pct_change(), funding, cfg, Costs())
    for k in ("sharpe", "max_drawdown", "ann_vol", "cagr"):
        assert np.isfinite(res[k])


def test_portfolios_yaml_loads():
    book = load_portfolios()
    assert {"carry", "neutral", "directional", "beta_lite"} <= set(book.cfgs)
