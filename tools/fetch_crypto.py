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
    p.add_argument("--symbols", required=True, help="comma-separated tickers, e.g. BTC,ETH,SOL")
    args = p.parse_args()
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
