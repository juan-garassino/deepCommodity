#!/usr/bin/env python
"""Fetch crypto prices + market caps. CoinGecko for market data; Binance for live ticker."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Binance/Alpaca style ticker -> CoinGecko id
GECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "AVAX": "avalanche-2",
    "LINK": "chainlink", "ATOM": "cosmos", "NEAR": "near", "INJ": "injective-protocol",
    "FET": "fetch-ai", "RNDR": "render-token", "TIA": "celestia", "JUP": "jupiter-exchange-solana",
}


def fetch_coingecko(symbols: list[str]) -> dict:
    ids = [GECKO_IDS.get(s.upper(), s.lower()) for s in symbols]
    r = requests.get(
        f"{COINGECKO_BASE}/coins/markets",
        params={"vs_currency": "usd", "ids": ",".join(ids), "price_change_percentage": "24h,7d"},
        timeout=15,
    )
    r.raise_for_status()
    rows = r.json()
    out: dict[str, dict] = {}
    for s, cg_id in zip(symbols, ids):
        match = next((row for row in rows if row.get("id") == cg_id), None)
        if not match:
            continue
        out[s.upper()] = {
            "symbol": s.upper(),
            "price_usd": match.get("current_price"),
            "market_cap_usd": match.get("market_cap"),
            "total_volume_usd": match.get("total_volume"),
            "pct_change_24h": match.get("price_change_percentage_24h_in_currency"),
            "pct_change_7d": match.get("price_change_percentage_7d_in_currency"),
        }
    return out


def fetch_top_n(n: int) -> dict:
    """Top-N by market cap from CoinGecko. Lets the agent operate dynamically
    without needing a pre-mapped ID for every symbol."""
    headers = {}
    if os.getenv("COINGECKO_API_KEY"):
        headers["x-cg-demo-api-key"] = os.environ["COINGECKO_API_KEY"]
    r = requests.get(
        f"{COINGECKO_BASE}/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": min(n, 250),
            "page": 1,
            "price_change_percentage": "24h,7d,30d",
            "sparkline": "false",
        },
        headers=headers, timeout=20,
    )
    r.raise_for_status()
    out: dict[str, dict] = {}
    for row in r.json():
        sym = (row.get("symbol") or "").upper()
        if not sym:
            continue
        out[sym] = {
            "symbol": sym,
            "price_usd": row.get("current_price"),
            "market_cap_usd": row.get("market_cap"),
            "total_volume_usd": row.get("total_volume"),
            "pct_change_24h": row.get("price_change_percentage_24h_in_currency"),
            "pct_change_7d": row.get("price_change_percentage_7d_in_currency"),
            "pct_change_30d": row.get("price_change_percentage_30d_in_currency"),
            "coingecko_id": row.get("id"),
        }
    return out


def maybe_binance_ticker(symbols: list[str]) -> dict:
    """Best-effort live ticker. Skipped silently if ccxt missing or auth fails."""
    if not os.getenv("BINANCE_API_KEY"):
        return {}
    try:
        import ccxt  # type: ignore
        client = ccxt.binance({"enableRateLimit": True})
        if os.getenv("BINANCE_TESTNET", "true").lower() == "true":
            client.set_sandbox_mode(True)
        out = {}
        for s in symbols:
            pair = f"{s.upper()}/USDT"
            try:
                t = client.fetch_ticker(pair)
                out[s.upper()] = {"binance_last": t.get("last"), "binance_bid": t.get("bid"),
                                  "binance_ask": t.get("ask")}
            except Exception:
                continue
        return out
    except Exception:
        return {}


def main() -> None:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--symbols",
                   help="comma-separated tickers, e.g. BTC,ETH,SOL")
    g.add_argument("--top-n", type=int,
                   help="fetch top N by market cap (1-250). Pulls dynamic universe.")
    args = p.parse_args()

    if args.top_n:
        if not (1 <= args.top_n <= 250):
            sys.exit("--top-n must be between 1 and 250")
        base = fetch_top_n(args.top_n)
    else:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
        if not symbols:
            sys.exit("no symbols")
        base = fetch_coingecko(symbols)
        live = maybe_binance_ticker(symbols)
        for sym, extra in live.items():
            base.setdefault(sym, {"symbol": sym}).update(extra)

    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "asset_class": "crypto",
        "symbols": base,
    }, indent=2))


if __name__ == "__main__":
    main()
