#!/usr/bin/env python
"""Fetch on-chain crypto metrics — exchange reserves, flows, miner data.

Tries CryptoQuant first (requires CRYPTOQUANT_API_KEY, free tier limited).
Fallback: derive a coarse exchange-flow proxy from Binance public klines —
days where BTC traded volume is unusually high vs 30d avg.

Output schema is consistent across providers; the agent reads `provider` to
calibrate confidence in the signal.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CQ_BASE = "https://api.cryptoquant.com/v1"


def fetch_cryptoquant(asset: str, metric: str, window: int) -> dict | None:
    key = os.getenv("CRYPTOQUANT_API_KEY")
    if not key:
        return None
    paths = {
        "exchange-reserve":   f"/btc/exchange-flows/reserve",
        "exchange-inflow":    f"/btc/exchange-flows/inflow",
        "miner-outflow":      f"/btc/miner-flows/outflow",
        "stablecoin-supply":  f"/usdt/network-data/supply",
    }
    p = paths.get(metric)
    if p is None:
        return None
    try:
        r = requests.get(f"{CQ_BASE}{p}",
                         headers={"Authorization": f"Bearer {key}"},
                         params={"window": "day", "limit": window,
                                 "exchange": "all_exchange"},
                         timeout=20)
        if r.status_code != 200:
            return {"error": f"cryptoquant {r.status_code}: {r.text[:120]}"}
        return r.json()
    except Exception as e:  # noqa: BLE001
        return {"error": f"cryptoquant fetch failed: {e}"}


def fetch_binance_volume_proxy(asset: str = "BTC", window: int = 30) -> dict:
    """Public Binance klines daily volume — coarse proxy for flow pressure."""
    pair = f"{asset.upper()}USDT"
    try:
        r = requests.get("https://api.binance.com/api/v3/klines",
                         params={"symbol": pair, "interval": "1d",
                                 "limit": window}, timeout=15)
        r.raise_for_status()
    except Exception as e:  # noqa: BLE001
        return {"error": f"binance fetch failed: {e}"}

    rows = r.json()
    daily = []
    for k in rows:
        ts = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).date().isoformat()
        volume = float(k[5])
        quote_volume = float(k[7])
        daily.append({"date": ts, "volume": volume, "quote_volume_usd": quote_volume})

    # Volume z-score: today's vol vs 30d mean+std
    if len(daily) >= 7:
        import statistics
        vols = [d["volume"] for d in daily]
        mean = statistics.mean(vols)
        sd = statistics.stdev(vols) if len(vols) > 1 else 0.0
        latest = daily[-1]["volume"]
        z = (latest - mean) / sd if sd > 0 else 0.0
        return {
            "asset": asset.upper(),
            "metric": "volume_zscore",
            "window_days": window,
            "latest_date": daily[-1]["date"],
            "latest_volume": latest,
            "mean_volume": mean,
            "z_score": round(z, 2),
            "interpretation": (
                "high-conviction selling pressure" if z > 2 and latest > mean
                else "elevated activity" if z > 1
                else "normal range"
            ),
            "daily": daily[-7:],   # last 7d only to keep payload small
        }
    return {"asset": asset.upper(), "metric": "volume_zscore", "daily": daily}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--asset", default="BTC", help="BTC | ETH (CryptoQuant) or any pair (Binance)")
    p.add_argument("--metric", default="exchange-reserve",
                   choices=["exchange-reserve", "exchange-inflow",
                            "miner-outflow", "stablecoin-supply", "volume-proxy"])
    p.add_argument("--window", type=int, default=30, help="days of history")
    args = p.parse_args()

    # Force volume-proxy if no CQ key, regardless of requested metric
    if args.metric == "volume-proxy" or not os.getenv("CRYPTOQUANT_API_KEY"):
        result = fetch_binance_volume_proxy(args.asset, args.window)
        provider = "binance-volume-proxy"
    else:
        result = fetch_cryptoquant(args.asset, args.metric, args.window)
        provider = "cryptoquant"
        if result is None or "error" in (result or {}):
            # Fallback to volume proxy
            result = fetch_binance_volume_proxy(args.asset, args.window)
            provider = "binance-volume-proxy"

    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": provider,
        "asset": args.asset.upper(),
        "metric": args.metric,
        "result": result,
    }, indent=2))


if __name__ == "__main__":
    main()
