#!/usr/bin/env python
"""Binance perpetual funding-rate history (public, no auth) for the carry sleeve.

Funding settles every 8h; a positive rate means longs pay shorts (so shorting the
perp earns it). We store the raw 8h rates per symbol; the backtester lags them to
settlement so nothing leaks. Source: GET fapi/v1/fundingRate.

Output: data/funding/<SYMBOL>.csv  (columns: fundingTime[ms], fundingRate)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
FAPI = "https://fapi.binance.com/fapi/v1/fundingRate"


def _to_pair(sym: str) -> str:
    s = sym.upper()
    return s if s.endswith("USDT") else f"{s}USDT"


def fetch_one(symbol: str, days: int) -> pd.DataFrame:
    pair = _to_pair(symbol)
    start = int((time.time() - days * 86400) * 1000)
    rows, cursor = [], start
    while True:
        r = requests.get(FAPI, params={"symbol": pair, "startTime": cursor, "limit": 1000}, timeout=30)
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        last = batch[-1]["fundingTime"]
        if len(batch) < 1000 or last <= cursor:
            break
        cursor = last + 1
    if not rows:
        return pd.DataFrame(columns=["fundingTime", "fundingRate"])
    df = pd.DataFrame(rows)[["fundingTime", "fundingRate"]]
    df["fundingRate"] = df["fundingRate"].astype(float)
    return df.drop_duplicates("fundingTime").sort_values("fundingTime")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", required=True, help="comma-separated, e.g. BTC,ETH,SOL")
    p.add_argument("--days", type=int, default=720)
    p.add_argument("--out-dir", default=str(ROOT / "data" / "funding"))
    args = p.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    summary = []
    for sym in syms:
        df = fetch_one(sym, args.days)
        if len(df):
            df.to_csv(out / f"{sym}.csv", index=False)
            summary.append(f"  {sym}: {len(df)} funding points -> {out / f'{sym}.csv'}")
        else:
            summary.append(f"  {sym}: no perp / no data (skipped)")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
