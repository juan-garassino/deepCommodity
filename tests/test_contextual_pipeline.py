"""Contextual forecaster — data pipeline + leakage + regime tests.

Motivating sources:
  tools/fetch_macro_features.py   (_lagged_daily, regime_readout, MACRO_FEATURE_COLS)
  tools/build_contextual_dataset.py (_build_one — point-in-time macro alignment)
No network / no torch here — synthetic inputs only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.fetch_macro_features import _lagged_daily, MACRO_FEATURE_COLS  # noqa: E402
from deepCommodity.model.contextual_transformer import regime_readout  # noqa: E402
from tools.build_contextual_dataset import _build_one  # noqa: E402


def test_lagged_daily_publishes_only_after_lag():
    # one observation on 2024-01-01; with a 10-day lag it must not be visible before 2024-01-11.
    idx = pd.date_range("2024-01-01", "2024-01-20", freq="D")
    raw = pd.Series([100.0], index=pd.to_datetime(["2024-01-01"]))
    out = _lagged_daily(raw, lag_days=10, index=idx)
    assert pd.isna(out.loc["2024-01-05"]) or out.loc["2024-01-05"] == 0 or np.isnan(out.loc["2024-01-05"])
    assert out.loc["2024-01-11"] == 100.0      # visible exactly at obs_date + lag
    assert out.loc["2024-01-15"] == 100.0      # and ffill'd forward


def test_regime_readout_directions():
    expanding = regime_readout({"netliq_chg4w": 0.03, "m2_yoy": 0.05, "dxy_chg4w": -0.01})
    contracting = regime_readout({"netliq_chg4w": -0.03, "m2_yoy": -0.02, "dxy_chg4w": 0.02})
    neutral = regime_readout({"netliq_chg4w": 0.01, "m2_yoy": -0.01, "dxy_chg4w": 0.0})
    assert expanding["regime"] == "EXPANDING"
    assert contracting["regime"] == "CONTRACTING"
    assert neutral["regime"] == "NEUTRAL"


def _synthetic_bars(n: int) -> pd.DataFrame:
    ts = pd.date_range("2020-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.sin(np.arange(n) / 5.0))
    return pd.DataFrame({"ts": ts.astype("int64") // 10**6, "open": close, "high": close * 1.01,
                         "low": close * 0.99, "close": close, "volume": np.arange(n) + 1.0})


def _synthetic_macro(n: int) -> pd.DataFrame:
    idx = pd.date_range("2019-06-01", periods=n + 400, freq="D")
    data = {c: np.linspace(0, 1, len(idx)) + 0.01 * np.arange(len(idx)) for c in MACRO_FEATURE_COLS}
    return pd.DataFrame(data, index=idx)


def test_build_one_shapes_and_no_lookahead(tmp_path):
    bars = _synthetic_bars(400)
    csv = tmp_path / "BTC.csv"
    bars.to_csv(csv, index=False)
    macro = _synthetic_macro(400)
    price_seq, macro_seq, weekly_h, daily_h = 90, 60, 10, 2

    part = _build_one("BTC", 0, csv, macro, price_seq, macro_seq, weekly_h, daily_h, 0.02, -0.02)
    assert part is not None
    assert part["price_X"].shape[1:] == (price_seq, 4)
    assert part["macro_X"].shape[1:] == (macro_seq, len(MACRO_FEATURE_COLS))
    assert len(part["price_X"]) == len(part["y_weekly"]) == len(part["dates"]) == len(part["r_weekly"])
    assert set(np.unique(part["y_weekly"])).issubset({0, 1, 2})

    # LEAKAGE: every macro window must end on or before its sample's as-of date.
    macro_idx = macro.index.normalize()
    for k in range(0, len(part["dates"]), 37):  # sample a few
        as_of = pd.Timestamp.fromordinal(int(part["dates"][k]))
        window_last = part["macro_X"][k][-1]
        expected_last = macro.loc[macro_idx <= as_of].iloc[-1].to_numpy()
        assert np.allclose(window_last, expected_last), "macro window leaked future data"
