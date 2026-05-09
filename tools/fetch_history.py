#!/usr/bin/env python
"""Pull historical OHLCV bars from public, unauthenticated endpoints.

Crypto: Binance public klines (no key needed).
Equities: yfinance (free, no key needed; falls back gracefully if uninstalled).

Output: per-symbol CSVs at data/bars/<SYMBOL>.csv with columns
        ts,open,high,low,close,volume
ready to feed `tools/backtest.py --bars-dir data/bars/`
or the price-transformer training pipeline.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "bars"

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"
INTERVAL_MS = {
    "1m": 60_000, "5m": 5*60_000, "15m": 15*60_000, "30m": 30*60_000,
    "1h": 60*60_000, "4h": 4*60*60_000, "1d": 24*60*60_000,
}


def fetch_binance(symbol: str, interval: str, start_ms: int, end_ms: int) -> list[list]:
    pair = symbol if symbol.endswith("USDT") else f"{symbol.upper()}USDT"
    out: list[list] = []
    cursor = start_ms
    step = INTERVAL_MS[interval] * 1000   # 1000 bars per call
    while cursor < end_ms:
        r = requests.get(BINANCE_KLINES, params={
            "symbol": pair, "interval": interval, "startTime": cursor,
            "endTime": min(end_ms, cursor + step), "limit": 1000,
        }, timeout=15)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            break
        out.extend(rows)
        cursor = rows[-1][0] + INTERVAL_MS[interval]
        time.sleep(0.1)   # gentle on the public endpoint
    return out


def fetch_equity(symbol: str, days: int, interval: str) -> list[list]:
    """yfinance fallback. Returns rows shaped like Binance klines:
       [open_ts_ms, open, high, low, close, volume, close_ts_ms]."""
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        sys.exit("yfinance not installed; pip install yfinance (no API key needed)")
    yf_interval = {"1h": "1h", "1d": "1d", "5m": "5m"}.get(interval, "1d")
    df = yf.Ticker(symbol).history(period=f"{days}d", interval=yf_interval)
    rows = []
    for ts, r in df.iterrows():
        ms = int(ts.timestamp() * 1000)
        rows.append([ms, float(r["Open"]), float(r["High"]), float(r["Low"]),
                     float(r["Close"]), float(r["Volume"]), ms])
    return rows


def write_csv(path: Path, rows: list[list]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "open", "high", "low", "close", "volume"])
        for r in rows:
            ts = datetime.fromtimestamp(r[0] / 1000, tz=timezone.utc).isoformat()
            w.writerow([ts, r[1], r[2], r[3], r[4], r[5]])
    return len(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", required=True,
                   help="comma-separated; e.g. BTC,ETH,SOL or AAPL,NVDA")
    p.add_argument("--asset-class", required=True, choices=["crypto", "equity"])
    p.add_argument("--interval", default="1h",
                   help="1m,5m,15m,30m,1h,4h,1d (binance) or 5m,1h,1d (yfinance)")
    p.add_argument("--days", type=int, default=365)
    p.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = p.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    out_dir = Path(args.out_dir)

    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=args.days)
    end_ms = int(end.timestamp() * 1000)
    start_ms = int(start.timestamp() * 1000)

    summary: list[tuple[str, int, str]] = []
    for sym in symbols:
        try:
            if args.asset_class == "crypto":
                rows = fetch_binance(sym, args.interval, start_ms, end_ms)
            else:
                rows = fetch_equity(sym, args.days, args.interval)
            n = write_csv(out_dir / f"{sym}.csv", rows)
            summary.append((sym, n, "OK"))
            print(f"  {sym}: {n} bars -> {out_dir / f'{sym}.csv'}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            summary.append((sym, 0, f"ERR: {e}"))
            print(f"  {sym}: FAILED ({e})", file=sys.stderr)

    print("\nSummary:", file=sys.stderr)
    for sym, n, status in summary:
        print(f"  {sym:<8} {n:>6} bars  {status}", file=sys.stderr)


if __name__ == "__main__":
    main()
