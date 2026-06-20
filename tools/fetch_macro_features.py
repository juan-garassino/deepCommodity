#!/usr/bin/env python
"""Global-macro feature panel for the contextual forecaster.

Pulls the slow "world liquidity regime" drivers and turns them into a daily,
**leakage-safe** feature table that the contextual model conditions on:

    M2 money supply        FRED WM2NS                 -> m2_yoy
    Net liquidity          FRED WALCL-RRPONTSYD-WTREGEN -> netliq_z, netliq_chg4w
    Broad USD index        FRED DTWEXBGS              -> dxy_z, dxy_chg4w
    Total crypto mcap      CoinGecko /global          -> totalcap_chg4w
    BTC dominance          CoinGecko /global          -> btc_dom

Leakage control: every series is shifted forward by its **publication lag** (the
value for calendar date D reflects only observations actually published on or
before D), then forward-filled to a daily index. All transforms are *causal*
(trailing rolling z-scores / point-in-time changes) so no future information
leaks into a feature. CoinGecko market-cap history is fetched from the public
market_chart endpoint (no key needed).

Output: data/macro/features.csv  (index=date, columns=MACRO_FEATURE_COLS)
Also prints a small JSON summary to stdout (latest row).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Feature columns the model consumes (order matters — it's the macro channel layout).
MACRO_FEATURE_COLS = [
    "m2_yoy",          # M2 year-over-year growth
    "netliq_z",        # net liquidity level, trailing z-score
    "netliq_chg4w",    # net liquidity 4-week change (normalized)
    "dxy_z",           # broad USD index level, trailing z-score
    "dxy_chg4w",       # USD 4-week change
    "totalcap_chg4w",  # total crypto market cap 4-week change
    "btc_dom",         # BTC dominance in [0,1]
]

# FRED series + assumed publication lag in days (conservative). See plan's leakage table.
FRED_SERIES = {
    "WM2NS": 10,        # M2, weekly, ~8-10d lag
    "WALCL": 7,         # Fed balance sheet, weekly
    "RRPONTSYD": 2,     # reverse repo, daily
    "WTREGEN": 2,       # Treasury General Account, daily
    "DTWEXBGS": 2,      # broad USD index, daily
}
ZSCORE_WINDOW = 252     # ~1 trading year, trailing
CHG_WINDOW = 28         # ~4 weeks


def _lagged_daily(series: pd.Series, lag_days: int, index: pd.DatetimeIndex) -> pd.Series:
    """Reindex a raw series to `index`, shifting observations forward by lag_days
    (so a value only becomes visible lag_days after its observation date), then ffill."""
    s = series.dropna().copy()
    s.index = pd.to_datetime(s.index) + pd.Timedelta(days=lag_days)
    return s.reindex(index.union(s.index)).sort_index().ffill().reindex(index)


def _trailing_z(s: pd.Series, window: int = ZSCORE_WINDOW) -> pd.Series:
    mean = s.rolling(window, min_periods=window // 4).mean()
    std = s.rolling(window, min_periods=window // 4).std()
    return ((s - mean) / std.replace(0, np.nan)).fillna(0.0)


def _fetch_fred(series_ids, start: str, end: str, api_key: str | None = None) -> pd.DataFrame:
    """FRED observations. Prefers the REST API when FRED_API_KEY is set, else falls
    back to the keyless public fredgraph.csv endpoint (no key needed)."""
    import io

    import requests
    cols = {}
    for sid in series_ids:
        s = None
        if api_key:
            try:
                r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                                 params={"series_id": sid, "api_key": api_key, "file_type": "json",
                                         "observation_start": start, "observation_end": end}, timeout=30)
                r.raise_for_status()
                s = pd.Series({pd.Timestamp(o["date"]): float(o["value"])
                               for o in r.json().get("observations", []) if o["value"] not in (".", "")})
            except Exception:
                s = None
        if s is None:  # keyless fallback
            r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                             params={"id": sid}, timeout=30)
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text))
            df.columns = ["date", "value"]
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            s = df.dropna().set_index(pd.to_datetime(df.dropna()["date"]))["value"]
        cols[sid] = s
    return pd.DataFrame(cols)


def _fetch_coingecko_global(days: int,
                            coins=("bitcoin", "ethereum", "solana")) -> pd.DataFrame:
    """Daily crypto market caps from CoinGecko's free market_chart endpoint.

    Free tier has no historical *global* total-cap, so we approximate crypto
    liquidity/breadth with the summed market caps of the traded universe and a
    real BTC dominance (BTC cap / universe cap) — both vary over time (unlike the
    pro-only global endpoint's flat fallback)."""
    import requests
    base = "https://api.coingecko.com/api/v3"
    key = os.getenv("COINGECKO_API_KEY")
    headers = {"x-cg-demo-api-key": key} if key else {}
    days = min(days, 365)   # CoinGecko free tier caps market_chart history at ~365d
    caps = {}
    for c in coins:
        js = requests.get(f"{base}/coins/{c}/market_chart",
                          params={"vs_currency": "usd", "days": days},
                          headers=headers, timeout=30).json()
        caps[c] = pd.Series({pd.Timestamp(ms, unit="ms").normalize(): v
                             for ms, v in js.get("market_caps", [])})
    df = pd.DataFrame(caps)
    if df.empty or "bitcoin" not in df:
        return pd.DataFrame({"totalcap": [], "btccap": []})
    return pd.DataFrame({"totalcap": df.sum(axis=1), "btccap": df["bitcoin"]})


def build_features(days: int) -> pd.DataFrame:
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days + ZSCORE_WINDOW + 60)  # extra history for trailing windows
    index = pd.date_range(start=str(start), end=str(end), freq="D")

    raw = _fetch_fred(list(FRED_SERIES), str(start), str(end), os.getenv("FRED_API_KEY"))

    lagged = {sid: _lagged_daily(raw[sid], lag, index) for sid, lag in FRED_SERIES.items()}

    # Net liquidity = WALCL(millions) - RRP(billions) - TGA(billions), harmonized to $bn.
    netliq = (lagged["WALCL"] / 1000.0) - lagged["RRPONTSYD"] - lagged["WTREGEN"]

    cg = _fetch_coingecko_global(days + 60)
    totalcap = cg["totalcap"].reindex(index).ffill()
    btc_dom = (cg["btccap"] / cg["totalcap"]).reindex(index).ffill().clip(0, 1).fillna(0.5)

    feats = pd.DataFrame(index=index)
    feats["m2_yoy"] = lagged["WM2NS"].pct_change(365).fillna(0.0)
    feats["netliq_z"] = _trailing_z(netliq)
    feats["netliq_chg4w"] = (netliq.pct_change(CHG_WINDOW)).fillna(0.0)
    feats["dxy_z"] = _trailing_z(lagged["DTWEXBGS"])
    feats["dxy_chg4w"] = lagged["DTWEXBGS"].pct_change(CHG_WINDOW).fillna(0.0)
    feats["totalcap_chg4w"] = totalcap.pct_change(CHG_WINDOW).fillna(0.0)
    feats["btc_dom"] = btc_dom
    feats = feats[MACRO_FEATURE_COLS].replace([np.inf, -np.inf], 0.0).fillna(0.0)
    # trim the warmup head used only for trailing windows
    return feats.loc[str(end - timedelta(days=days)):]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=2200, help="days of daily history to emit")
    p.add_argument("--out", default=str(ROOT / "data" / "macro" / "features.csv"))
    args = p.parse_args()
    feats = build_features(args.days)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    feats.to_csv(out, index_label="date")

    last = feats.iloc[-1] if len(feats) else pd.Series(dtype=float)
    print(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "out": str(out), "rows": len(feats), "cols": MACRO_FEATURE_COLS,
        "latest": {c: round(float(last[c]), 6) for c in MACRO_FEATURE_COLS} if len(feats) else {},
    }, indent=2))


if __name__ == "__main__":
    main()
