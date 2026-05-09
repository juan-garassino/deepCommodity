#!/usr/bin/env python
"""Pull historical aggregate trades from Binance public REST.

Endpoint: /api/v3/aggTrades (no auth, 1000 trades per call).
We aggregate to per-second bars: signed_volume, trade_count, mean_size, vwap_drift.

Output: data/orderflow/<SYMBOL>.csv with columns
    ts,signed_volume,trade_count,mean_size,vwap_drift
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "orderflow"
AGG_TRADES = "https://api.binance.com/api/v3/aggTrades"


def fetch_agg_trades(pair: str, start_ms: int, end_ms: int) -> list[dict]:
    """Iterate aggTrades until the entire window is covered."""
    out: list[dict] = []
    cursor = start_ms
    while cursor < end_ms:
        r = requests.get(AGG_TRADES, params={
            "symbol": pair, "startTime": cursor,
            "endTime": min(end_ms, cursor + 60 * 60_000),  # 1h chunks
            "limit": 1000,
        }, timeout=15)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            cursor += 60_000     # advance 1 minute and retry on empty
            continue
        out.extend(rows)
        last_ts = rows[-1]["T"]
        if last_ts <= cursor:
            cursor += 60_000     # break stalls
        else:
            cursor = last_ts + 1
        time.sleep(0.15)
    return out


def aggregate_per_second(trades: list[dict]) -> list[list]:
    """Bucket trades by second; produce [ts, signed_vol, n_trades, mean_size, vwap_drift]."""
    buckets: dict[int, list] = defaultdict(list)
    for t in trades:
        sec = t["T"] // 1000
        price = float(t["p"])
        qty = float(t["q"])
        # m=True means the buyer is the maker, so the trade was a SELL (taker hit bid)
        signed = -qty if t.get("m") else qty
        buckets[sec].append((price, qty, signed))

    rows: list[list] = []
    prev_vwap: float | None = None
    for sec in sorted(buckets):
        items = buckets[sec]
        signed_vol = sum(s for _, _, s in items)
        n = len(items)
        total_qty = sum(q for _, q, _ in items) or 1e-12
        vwap = sum(p * q for p, q, _ in items) / total_qty
        mean_size = total_qty / n
        drift = 0.0 if prev_vwap is None else (vwap - prev_vwap) / prev_vwap
        prev_vwap = vwap
        rows.append([sec, signed_vol, n, mean_size, drift])
    return rows


def write_csv(path: Path, rows: list[list]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "signed_volume", "trade_count", "mean_size", "vwap_drift"])
        for r in rows:
            ts = datetime.fromtimestamp(r[0], tz=timezone.utc).isoformat()
            w.writerow([ts, r[1], r[2], r[3], r[4]])
    return len(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", required=True, help="comma-separated, e.g. BTC,ETH")
    p.add_argument("--hours", type=int, default=24,
                   help="how many hours of trade tape (default 24; 1h ≈ 50–500MB raw on BTC)")
    p.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(hours=args.hours)
    end_ms = int(end.timestamp() * 1000)
    start_ms = int(start.timestamp() * 1000)

    for sym in [s.strip().upper() for s in args.symbols.split(",")]:
        pair = f"{sym}USDT"
        try:
            trades = fetch_agg_trades(pair, start_ms, end_ms)
            rows = aggregate_per_second(trades)
            n = write_csv(out_dir / f"{sym}.csv", rows)
            print(f"  {sym}: {len(trades)} trades -> {n} second-bars", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  {sym}: FAILED ({e})", file=sys.stderr)


if __name__ == "__main__":
    main()
