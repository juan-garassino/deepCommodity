#!/usr/bin/env python
"""Fetch insider transactions from OpenInsider.

OpenInsider aggregates SEC Form 4 filings and surfaces 'cluster buys' — when
multiple insiders buy the same stock in a short window. Cluster buys are one
of the highest-conviction predictive signals in equities.

No API key. Public scrape with a polite User-Agent.

Default: returns the last 14 days of cluster buys.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.guardrails.sanitize import sanitize_news  # noqa: E402

CLUSTER_BUYS_URL = "http://openinsider.com/latest-cluster-buys"
LATEST_BUYS_URL = "http://openinsider.com/latest-insider-purchases-25k"
USER_AGENT = "deepCommodity-research/1.0 (+contact-via-github)"


def fetch_html(url: str, timeout: float = 20.0) -> str:
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    r.raise_for_status()
    return r.text


# OpenInsider's HTML tables follow a stable column layout. Parse with regex
# rather than BeautifulSoup to avoid an extra dep.
ROW_RE = re.compile(
    r"<tr[^>]*>\s*"
    r"(?:<td[^>]*>.*?</td>\s*){2}"                         # X marks (skip 2 cols)
    r"<td[^>]*>(?P<filing>[^<]+)</td>\s*"                   # filing date/time
    r"<td[^>]*>(?P<txn_date>[^<]+)</td>\s*"                 # txn date
    r"<td[^>]*><a[^>]*>(?P<ticker>[A-Z\.\-]+)</a></td>\s*"  # ticker
    r"<td[^>]*>(?P<company>[^<]*)</td>\s*"                  # company
    r"<td[^>]*>(?P<insider>[^<]*)</td>\s*"                  # insider
    r"<td[^>]*>(?P<role>[^<]*)</td>\s*"                     # role
    r"(?:<td[^>]*>.*?</td>\s*){2}"                          # txn type, ?
    r"<td[^>]*>(?P<price>[^<]*)</td>\s*"                    # price
    r"(?:<td[^>]*>.*?</td>\s*){2}"                          # qty, owned
    r"<td[^>]*>(?P<value>[^<]*)</td>",                      # value
    re.DOTALL,
)


def parse(html: str, max_rows: int = 50) -> list[dict]:
    out: list[dict] = []
    for m in ROW_RE.finditer(html):
        row = m.groupdict()
        ticker = row["ticker"].strip()
        if not ticker:
            continue
        out.append({
            "ticker": ticker,
            "company": sanitize_news(row["company"].strip()),
            "filing_date": row["filing"].strip(),
            "txn_date": row["txn_date"].strip(),
            "insider": sanitize_news(row["insider"].strip()),
            "role": row["role"].strip(),
            "price": row["price"].strip(),
            "value_usd": row["value"].strip().replace("$", "").replace(",", ""),
        })
        if len(out) >= max_rows:
            break
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["cluster", "latest"], default="cluster",
                   help="cluster = multiple insiders same week (high signal); "
                        "latest = recent purchases > $25k")
    p.add_argument("--max", type=int, default=30, help="max rows returned")
    p.add_argument("--symbols",
                   help="optional filter: comma-separated tickers; only return "
                        "rows where ticker is in this list")
    args = p.parse_args()

    url = CLUSTER_BUYS_URL if args.mode == "cluster" else LATEST_BUYS_URL
    try:
        html = fetch_html(url)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "mode": args.mode,
            "error": f"fetch failed: {e}",
            "rows": [],
        }, indent=2))
        sys.exit(0)

    rows = parse(html, max_rows=args.max * 2)
    if args.symbols:
        wanted = {s.strip().upper() for s in args.symbols.split(",")}
        rows = [r for r in rows if r["ticker"].upper() in wanted]
    rows = rows[: args.max]

    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "openinsider",
        "mode": args.mode,
        "n_rows": len(rows),
        "rows": rows,
    }, indent=2))


if __name__ == "__main__":
    main()
