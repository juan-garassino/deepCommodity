#!/usr/bin/env python
"""Fetch upcoming earnings calendar from Finnhub (free key, 60 req/min).

Helps the agent avoid blind earnings entries — if NVDA reports tomorrow AMC,
don't open a fresh position today. Also flags imminent catalysts.

Falls back to yfinance per-ticker `.calendar` if no FINNHUB_API_KEY set.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FINNHUB_URL = "https://finnhub.io/api/v1/calendar/earnings"


def fetch_finnhub(symbols: list[str], days: int) -> list[dict]:
    key = os.getenv("FINNHUB_API_KEY")
    if not key:
        return []
    today = datetime.now(timezone.utc).date()
    horizon = today + timedelta(days=days)
    r = requests.get(FINNHUB_URL, params={
        "from": str(today),
        "to": str(horizon),
        "token": key,
    }, timeout=20)
    r.raise_for_status()
    data = r.json().get("earningsCalendar", []) or []
    if symbols:
        wanted = {s.upper() for s in symbols}
        data = [e for e in data if (e.get("symbol") or "").upper() in wanted]
    return [{
        "symbol": e.get("symbol"),
        "date": e.get("date"),
        "hour": e.get("hour"),       # bmo / amc
        "year": e.get("year"),
        "quarter": e.get("quarter"),
        "eps_estimate": e.get("epsEstimate"),
        "eps_actual": e.get("epsActual"),
        "revenue_estimate": e.get("revenueEstimate"),
        "revenue_actual": e.get("revenueActual"),
    } for e in data]


def fetch_yfinance(symbols: list[str], days: int) -> list[dict]:
    """Fallback: per-ticker calendar via yfinance."""
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        return []
    today = datetime.now(timezone.utc).date()
    horizon = today + timedelta(days=days)
    out: list[dict] = []
    for sym in symbols:
        try:
            t = yf.Ticker(sym)
            cal = t.calendar
            if cal is None or cal.empty if hasattr(cal, "empty") else not cal:
                continue
            # yfinance returns either DataFrame or dict depending on version
            ed = None
            if isinstance(cal, dict):
                ed = (cal.get("Earnings Date") or [None])
                ed = ed[0] if isinstance(ed, list) and ed else ed
            else:
                ed = cal.iloc[0]["Earnings Date"] if "Earnings Date" in cal.columns else None
            if ed is None:
                continue
            ed_date = ed.date() if hasattr(ed, "date") else ed
            if today <= ed_date <= horizon:
                out.append({"symbol": sym.upper(), "date": str(ed_date),
                            "source": "yfinance"})
        except Exception:  # noqa: BLE001
            continue
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", default="",
                   help="comma-separated tickers (filter); empty = all in horizon")
    p.add_argument("--days", type=int, default=14,
                   help="horizon in days (default 14)")
    args = p.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    rows = fetch_finnhub(symbols, args.days)
    provider = "finnhub"
    if not rows:
        rows = fetch_yfinance(symbols, args.days)
        provider = "yfinance" if rows else "none"

    rows.sort(key=lambda r: r.get("date") or "9999-99-99")

    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": provider,
        "horizon_days": args.days,
        "n_rows": len(rows),
        "upcoming": rows,
    }, indent=2))


if __name__ == "__main__":
    main()
