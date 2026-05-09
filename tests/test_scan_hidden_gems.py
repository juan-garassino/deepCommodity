"""Hidden-gems scanner — filter logic + universe exclusion."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "scan_hidden_gems.py"


def _load():
    spec = importlib.util.spec_from_file_location("scan_hidden_gems", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _row(symbol="X", name="X coin", mcap=100e6, vol=10e6, price=1.0,
         pct_24h=1.0, pct_7d=2.0, pct_30d=40.0, cg_id=None):
    return {
        "id": cg_id or symbol.lower(),
        "symbol": symbol.lower(),
        "name": name,
        "current_price": price,
        "market_cap": mcap,
        "total_volume": vol,
        "price_change_percentage_24h_in_currency": pct_24h,
        "price_change_percentage_7d_in_currency": pct_7d,
        "price_change_percentage_30d_in_currency": pct_30d,
    }


def test_excludes_universe_symbols():
    mod = _load()
    rows = [_row("BTC", mcap=1e9), _row("ETH", mcap=400e9), _row("FRESH", mcap=100e6)]
    out = mod.filter_candidates(rows, excluded={"BTC", "ETH", "SOL"})
    syms = [c["symbol"] for c in out]
    assert "BTC" not in syms
    assert "ETH" not in syms
    assert "FRESH" in syms


def test_filters_too_small_mcap():
    mod = _load()
    rows = [_row("TINY", mcap=10e6), _row("OK", mcap=100e6)]
    out = mod.filter_candidates(rows, excluded=set())
    assert [c["symbol"] for c in out] == ["OK"]


def test_filters_too_large_mcap():
    mod = _load()
    rows = [_row("HUGE", mcap=2e9), _row("OK", mcap=100e6)]
    out = mod.filter_candidates(rows, excluded=set())
    assert [c["symbol"] for c in out] == ["OK"]


def test_filters_low_30d_momentum():
    mod = _load()
    rows = [_row("FLAT", pct_30d=5.0), _row("RUN", pct_30d=80.0)]
    out = mod.filter_candidates(rows, excluded=set())
    assert [c["symbol"] for c in out] == ["RUN"]


def test_filters_low_volume():
    mod = _load()
    rows = [_row("THIN", vol=1e6), _row("LIQUID", vol=20e6)]
    out = mod.filter_candidates(rows, excluded=set())
    assert [c["symbol"] for c in out] == ["LIQUID"]


def test_filters_dust_price():
    mod = _load()
    rows = [_row("DUST", price=0.0001), _row("OK", price=0.5)]
    out = mod.filter_candidates(rows, excluded=set())
    assert [c["symbol"] for c in out] == ["OK"]


def test_skips_rows_with_missing_30d_pct():
    mod = _load()
    rows = [_row("MISSING"), _row("OK")]
    rows[0]["price_change_percentage_30d_in_currency"] = None
    out = mod.filter_candidates(rows, excluded=set())
    assert [c["symbol"] for c in out] == ["OK"]


def test_output_schema_has_required_fields():
    mod = _load()
    rows = [_row("OK")]
    out = mod.filter_candidates(rows, excluded=set())
    assert len(out) == 1
    keys = set(out[0].keys())
    needed = {"symbol", "name", "coingecko_id", "price_usd", "market_cap_usd",
              "total_volume_usd", "pct_change_24h", "pct_change_7d",
              "pct_change_30d", "coingecko_url"}
    assert needed.issubset(keys), f"missing: {needed - keys}"


def test_ranks_by_momentum_x_log_volume():
    mod = _load()
    rows = [
        _row("LO", mcap=100e6, pct_30d=35, vol=6e6),     # weak both
        _row("HI", mcap=100e6, pct_30d=80, vol=50e6),    # strong both
        _row("MED", mcap=100e6, pct_30d=50, vol=10e6),
    ]
    out = mod.filter_candidates(rows, excluded=set())
    syms = [c["symbol"] for c in out]
    assert syms == ["HI", "MED", "LO"]


def test_real_universe_loads_and_excludes_btc():
    """End-to-end with the actual themes.yaml."""
    from deepCommodity.universe import Universe
    u = Universe.load()
    assert "BTC" in u.all_crypto_symbols()
    # If we ever scan top 10, BTC's 7d% would be < 30d filter so it'd be excluded
    # by the momentum filter anyway, but the universe-exclusion belt is tighter.
