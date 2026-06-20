"""Portfolio research: market-neutral L/S + funding carry, with risk-managed presets.

Offline (research/backtest) only — no live execution here. Loaders return aligned
date×symbol panels the sleeves/backtester consume.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def _load_bars_close(csv: Path) -> pd.Series | None:
    if not csv.exists():
        return None
    df = pd.read_csv(csv)
    if np.issubdtype(df["ts"].dtype, np.number):
        idx = pd.to_datetime(df["ts"], unit="ms")
    else:
        idx = pd.to_datetime(df["ts"], utc=True).dt.tz_localize(None)
    return pd.Series(df["close"].astype(float).values, index=idx.dt.normalize())


def load_prices(symbols, bars_dir: Path) -> pd.DataFrame:
    """date×symbol daily close panel (inner-aligned on common dates)."""
    cols = {}
    for s in symbols:
        c = _load_bars_close(Path(bars_dir) / f"{s}.csv")
        if c is not None and len(c) > 60:
            cols[s] = c[~c.index.duplicated(keep="last")]
    if not cols:
        raise SystemExit("no usable bars — fetch daily bars first")
    return pd.DataFrame(cols).sort_index().dropna(how="all")


def load_funding(symbols, funding_dir: Path, index: pd.DatetimeIndex) -> pd.DataFrame:
    """date×symbol DAILY funding (sum of the day's 8h rates), reindexed to `index`.

    Lagged one day so a day's funding is only known the next day (causal)."""
    out = pd.DataFrame(0.0, index=index, columns=list(symbols))
    for s in symbols:
        csv = Path(funding_dir) / f"{s}.csv"
        if not csv.exists():
            continue
        f = pd.read_csv(csv)
        f["d"] = pd.to_datetime(f["fundingTime"], unit="ms").dt.normalize()
        daily = f.groupby("d")["fundingRate"].sum()
        out[s] = daily.reindex(index).shift(1).fillna(0.0)
    return out


def load_regime(macro_csv: Path, index: pd.DatetimeIndex) -> pd.Series:
    """Regime sign in {-1,0,+1} per date from the macro panel (causal)."""
    from deepCommodity.model.contextual_transformer import regime_readout
    from tools.fetch_macro_features import MACRO_FEATURE_COLS
    if not Path(macro_csv).exists():
        return pd.Series(0, index=index)
    m = pd.read_csv(macro_csv, index_col="date", parse_dates=True)[MACRO_FEATURE_COLS]
    m.index = m.index.normalize()
    m = m.reindex(index).ffill()
    score = m.apply(lambda r: {"EXPANDING": 1, "CONTRACTING": -1}.get(
        regime_readout(r.to_dict())["regime"], 0), axis=1)
    return score.fillna(0).astype(int)
