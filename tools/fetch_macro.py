#!/usr/bin/env python
"""Thin wrapper over deepCommodity.sourcing.api_sourcing_boilerplate.retrieve_fred_data."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--series", required=True,
                   help="comma-separated FRED series ids, e.g. CPIAUCSL,UNRATE,DGS10")
    p.add_argument("--days", type=int, default=365)
    args = p.parse_args()
    series = [s.strip() for s in args.series.split(",") if s.strip()]
    if not os.getenv("FRED_API_KEY"):
        sys.exit("FRED_API_KEY not set")

    from deepCommodity.sourcing.api_sourcing_boilerplate import retrieve_fred_data

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=args.days)
    df = retrieve_fred_data(series, str(start), str(end), frequency="d")
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "series": series,
        "rows": len(df),
        "latest": {col: float(df[col].iloc[-1]) for col in df.columns} if len(df) else {},
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
