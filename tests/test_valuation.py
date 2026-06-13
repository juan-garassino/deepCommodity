"""Pure crypto-balance valuation (audit fix B5): NAV/positions/cash in USD."""
from __future__ import annotations

import math

import pytest

from deepCommodity.execution._valuation import value_crypto_balances
from deepCommodity.util import envbool


def test_values_non_stable_via_tickers():
    totals = {"BTC": 0.5, "USDT": 1000.0}
    free = {"USDT": 1000.0}
    tickers = {"BTC/USDT": {"last": 60000.0}}
    nav, positions, cash = value_crypto_balances(totals, free, tickers)
    assert nav == pytest.approx(31000.0)          # 0.5*60000 + 1000
    assert positions == {"BTC": pytest.approx(30000.0)}  # USD notional, not 0.5
    assert cash == pytest.approx(1000.0)           # free USDT


def test_stables_count_as_cash_and_nav():
    nav, positions, cash = value_crypto_balances(
        {"USDC": 500.0, "USDT": 250.0}, {"USDC": 500.0, "USDT": 250.0}, {}
    )
    assert nav == pytest.approx(750.0)
    assert positions == {}
    assert cash == pytest.approx(750.0)


def test_ignores_zero_and_dust():
    nav, positions, cash = value_crypto_balances(
        {"BTC": 0.0, "USDT": 100.0}, {"USDT": 100.0}, {"BTC/USDT": {"last": 60000.0}}
    )
    assert positions == {}
    assert nav == pytest.approx(100.0)


def test_nav_equals_sum_positions_plus_cash():
    totals = {"ETH": 2.0, "USDT": 500.0}
    tickers = {"ETH/USDT": {"last": 3000.0}}
    nav, positions, cash = value_crypto_balances(totals, {"USDT": 500.0}, tickers)
    assert nav == pytest.approx(sum(positions.values()) + cash)


def test_envbool_true_variants():
    import os
    for v in ("true", "True", " TRUE ", "1", "yes", "YES"):
        os.environ["DC_TEST_BOOL"] = v
        assert envbool("DC_TEST_BOOL") is True
    for v in ("false", "0", "no", "", "  "):
        os.environ["DC_TEST_BOOL"] = v
        assert envbool("DC_TEST_BOOL") is False
    del os.environ["DC_TEST_BOOL"]
    assert envbool("DC_TEST_BOOL", default=True) is True
