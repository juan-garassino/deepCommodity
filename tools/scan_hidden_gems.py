#!/usr/bin/env python
"""Scan CoinGecko top 250 by market cap for low-cap momentum candidates.

Filters:
  - $30M <= market_cap <= $500M
  - 30d % change >= 30
  - 24h volume >= $5M
  - price >= $0.001
  - NOT already in the universe (anchors / large_cap / mid_cap) — gems must be fresh

Returns 0-10 candidates. Each carries a short CoinGecko description so the
agent can write a real thesis before the candidate qualifies for risk_check.
The gem lane is gated separately by the routine: rank score >= 0.65 AND
agent thesis >= 100 chars citing news.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.universe import Universe  # noqa: E402

COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_COIN = "https://api.coingecko.com/api/v3/coins/{id}"


def fetch_top_n(n: int = 250) -> list[dict]:
    """One paginated call. CoinGecko allows up to 250 per page."""
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": min(n, 250),
        "page": 1,
        "price_change_percentage": "24h,7d,30d",
        "sparkline": "false",
    }
    headers = {}
    if os.getenv("COINGECKO_API_KEY"):
        headers["x-cg-demo-api-key"] = os.environ["COINGECKO_API_KEY"]
    r = requests.get(COINGECKO_MARKETS, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_description(coin_id: str) -> str:
    """Fetch the short English description. Best-effort; returns '' on any failure."""
    try:
        headers = {}
        if os.getenv("COINGECKO_API_KEY"):
            headers["x-cg-demo-api-key"] = os.environ["COINGECKO_API_KEY"]
        r = requests.get(
            COINGECKO_COIN.format(id=coin_id),
            params={"localization": "false", "tickers": "false",
                    "market_data": "false", "community_data": "false",
                    "developer_data": "false"},
            headers=headers, timeout=15,
        )
        if r.status_code != 200:
            return ""
        desc = (r.json().get("description") or {}).get("en", "") or ""
        return desc.split(".")[0][:300]   # first sentence, max 300 chars
    except Exception:  # noqa: BLE001
        return ""


def filter_candidates(rows: list[dict], excluded: set[str],
                      min_mcap: float = 30e6,
                      max_mcap: float = 500e6,
                      min_30d_pct: float = 30.0,
                      min_volume: float = 5e6,
                      min_price: float = 0.001) -> list[dict]:
    out = []
    for row in rows:
        sym = (row.get("symbol") or "").upper()
        if not sym or sym in excluded:
            continue
        mcap = row.get("market_cap") or 0
        vol = row.get("total_volume") or 0
        price = row.get("current_price") or 0
        pct_30d = row.get("price_change_percentage_30d_in_currency")
        if pct_30d is None:
            continue
        if not (min_mcap <= mcap <= max_mcap):
            continue
        if pct_30d < min_30d_pct:
            continue
        if vol < min_volume:
            continue
        if price < min_price:
            continue
        out.append({
            "symbol": sym,
            "name": row.get("name"),
            "coingecko_id": row.get("id"),
            "price_usd": price,
            "market_cap_usd": mcap,
            "total_volume_usd": vol,
            "pct_change_24h": row.get("price_change_percentage_24h_in_currency"),
            "pct_change_7d": row.get("price_change_percentage_7d_in_currency"),
            "pct_change_30d": pct_30d,
            "coingecko_url": f"https://www.coingecko.com/en/coins/{row.get('id')}",
        })
    # rank by 30d momentum × log10(volume) — higher = stronger candidate
    import math
    out.sort(key=lambda x: x["pct_change_30d"] * math.log10(max(x["total_volume_usd"], 1)),
             reverse=True)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--top-n", type=int, default=250)
    p.add_argument("--max", type=int, default=10, help="max candidates returned")
    p.add_argument("--with-descriptions", action="store_true",
                   help="fetch CoinGecko description per candidate (slower, +1 API call each)")
    p.add_argument("--min-mcap", type=float, default=30e6)
    p.add_argument("--max-mcap", type=float, default=500e6)
    p.add_argument("--min-30d-pct", type=float, default=30.0)
    p.add_argument("--min-volume", type=float, default=5e6)
    args = p.parse_args()

    u = Universe.load()
    excluded = u.all_crypto_symbols()

    rows = fetch_top_n(args.top_n)
    cands = filter_candidates(rows, excluded,
                              min_mcap=args.min_mcap, max_mcap=args.max_mcap,
                              min_30d_pct=args.min_30d_pct,
                              min_volume=args.min_volume)
    cands = cands[: args.max]

    if args.with_descriptions:
        for c in cands:
            c["description"] = fetch_description(c["coingecko_id"])
            time.sleep(0.2)   # gentle on the public API

    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "filters": {
            "min_mcap": args.min_mcap, "max_mcap": args.max_mcap,
            "min_30d_pct": args.min_30d_pct, "min_volume": args.min_volume,
        },
        "excluded_universe_size": len(excluded),
        "candidates": cands,
    }, indent=2))


if __name__ == "__main__":
    main()
