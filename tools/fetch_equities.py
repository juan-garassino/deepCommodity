#!/usr/bin/env python
"""Fetch US equity bars + latest quote + market cap via Alpaca."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone


def _alpaca_clients():
    try:
        from alpaca.data.historical import StockHistoricalDataClient  # type: ignore
        from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest  # type: ignore
        from alpaca.data.timeframe import TimeFrame  # type: ignore
        from alpaca.data.enums import DataFeed  # type: ignore
        from alpaca.trading.client import TradingClient  # type: ignore
    except ImportError as e:
        sys.exit(f"alpaca-py not installed: {e}")
    key = os.getenv("ALPACA_API_KEY", "")
    sec = os.getenv("ALPACA_API_SECRET", "")
    if not key or not sec:
        sys.exit("ALPACA_API_KEY / ALPACA_API_SECRET not set")
    paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"
    return (
        StockHistoricalDataClient(api_key=key, secret_key=sec),
        TradingClient(api_key=key, secret_key=sec, paper=paper),
        StockBarsRequest, StockLatestQuoteRequest, TimeFrame, DataFeed,
    )


def fetch(symbols: list[str]) -> dict:
    data, trading, BarsReq, QuoteReq, TF, DataFeed = _alpaca_clients()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=10)
    # Free Alpaca accounts can only use the IEX feed for stocks; SIP requires a
    # paid subscription. Override via ALPACA_DATA_FEED=sip if you have that.
    feed_name = os.getenv("ALPACA_DATA_FEED", "iex").lower()
    feed = DataFeed.SIP if feed_name == "sip" else DataFeed.IEX
    bars = data.get_stock_bars(BarsReq(symbol_or_symbols=symbols, timeframe=TF.Day,
                                       start=start, end=end, feed=feed))
    quotes = data.get_stock_latest_quote(QuoteReq(symbol_or_symbols=symbols, feed=feed))

    out: dict[str, dict] = {}
    for s in symbols:
        sym_bars = list(bars.data.get(s, []))
        if not sym_bars:
            continue
        first, last = sym_bars[0], sym_bars[-1]
        pct_7d = (last.close - first.close) / first.close * 100 if first.close else None
        try:
            asset = trading.get_asset(s)
            mcap = float(getattr(asset, "market_cap", 0) or 0) or None
        except Exception:
            mcap = None
        q = quotes.get(s) if hasattr(quotes, "get") else getattr(quotes, s, None)
        out[s] = {
            "symbol": s,
            "price_usd": last.close,
            "market_cap_usd": mcap,
            "volume": last.volume,
            "pct_change_7d": pct_7d,
            "bid": getattr(q, "bid_price", None),
            "ask": getattr(q, "ask_price", None),
        }
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", required=True)
    args = p.parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    if not symbols:
        sys.exit("no symbols")
    out = fetch(symbols)
    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "asset_class": "equity",
        "symbols": out,
    }, indent=2))


if __name__ == "__main__":
    main()
