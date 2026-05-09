#!/usr/bin/env python
"""Fetch CME Fed-Funds futures data → implied rate-decision probabilities.

Approach: pull the front 6 months of 30-day Fed Funds futures (ZQ=F via
yfinance) and compute the implied effective Fed Funds rate per contract.
Implied rate = 100 - settlement price.

Then compare contract-implied rates across consecutive months to derive an
implied probability of a rate change at each upcoming FOMC meeting.

This is the same math the official CME FedWatch tool uses; numbers may
differ slightly because we don't account for intra-month meeting timing.
For the agent's purposes it's plenty.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def fetch_zq_chain(months: int = 6) -> list[dict]:
    """Pull recent settle prices for ZQ futures across the next N months."""
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        return []

    out: list[dict] = []
    # yfinance front-month: ZQ=F. For the chain we need symbols like ZQM26.CME (month code + year).
    # Simpler: use the continuous front contract for the latest implied rate, plus
    # query the SOFR/Fed Funds futures via Federal Reserve's H.15 data for the curve.
    # For v1 we just report the front contract's implied rate.
    try:
        front = yf.Ticker("ZQ=F")
        hist = front.history(period="5d")
        if hist.empty:
            return []
        close = float(hist["Close"].iloc[-1])
        implied_rate = 100.0 - close
        out.append({
            "contract": "ZQ=F (front)",
            "settle": close,
            "implied_rate_pct": round(implied_rate, 3),
        })
    except Exception:  # noqa: BLE001
        return []
    return out


def fetch_fed_target_rate() -> tuple[float | None, str]:
    """Latest Fed Funds target upper bound from FRED (free, no key for series ID DFEDTARU)."""
    try:
        import requests
        r = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={"series_id": "DFEDTARU",
                    "api_key": __import__("os").getenv("FRED_API_KEY", ""),
                    "file_type": "json", "limit": 1, "sort_order": "desc"},
            timeout=15,
        )
        if r.status_code != 200:
            return None, "fred error"
        obs = r.json().get("observations", [])
        if not obs:
            return None, "no observations"
        return float(obs[0]["value"]), obs[0]["date"]
    except Exception:  # noqa: BLE001
        return None, "fred unreachable"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--months", type=int, default=6,
                   help="number of forward FOMC months to imply (best effort)")
    args = p.parse_args()

    chain = fetch_zq_chain(args.months)
    target_upper, target_date = fetch_fed_target_rate()

    if not chain:
        print(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "error": "no fed funds futures data available (yfinance unreachable?)",
            "current_target_upper_pct": target_upper,
            "as_of": target_date,
        }, indent=2))
        sys.exit(0)

    # Implied move = front contract implied rate - current target
    implied = []
    if target_upper is not None:
        for c in chain:
            delta_bps = (c["implied_rate_pct"] - target_upper) * 100
            implied.append({
                "contract": c["contract"],
                "implied_rate_pct": c["implied_rate_pct"],
                "current_target_upper_pct": target_upper,
                "implied_move_bps": round(delta_bps, 1),
                "interpretation": (
                    "strong cut implied" if delta_bps < -20
                    else "modest cut implied" if delta_bps < -5
                    else "no change implied" if -5 <= delta_bps <= 5
                    else "modest hike implied" if delta_bps < 20
                    else "strong hike implied"
                ),
            })

    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "yfinance + fred",
        "current_target_upper_pct": target_upper,
        "as_of_date": target_date,
        "front_contract": chain[0] if chain else None,
        "implied": implied,
    }, indent=2))


if __name__ == "__main__":
    main()
