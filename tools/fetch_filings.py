#!/usr/bin/env python
"""Fetch recent SEC EDGAR 8-K filings for given tickers.

8-Ks are filed for material corporate events: M&A, exec changes, contract
wins/losses, earnings pre-announcements, regulatory actions. Real-time signal,
freely available, ~10 req/sec rate limit.

Two-step:
  1. Resolve tickers -> CIKs via SEC's company_tickers.json (cached at /tmp).
  2. Pull each CIK's recent 8-Ks via the EDGAR Atom feed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.guardrails.sanitize import sanitize_news  # noqa: E402

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
EDGAR_FEED_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcompany&CIK={cik}&type=8-K&dateb=&owner=include&count=10&output=atom"
)
USER_AGENT = "deepCommodity-research research@deepcommodity.local"
CACHE_PATH = Path("/tmp/dc_sec_ticker_map.json")
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def load_ticker_map() -> dict[str, str]:
    """ticker -> 10-digit zero-padded CIK string."""
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except Exception:  # noqa: BLE001
            pass
    r = requests.get(TICKER_MAP_URL,
                     headers={"User-Agent": USER_AGENT}, timeout=20)
    r.raise_for_status()
    raw = r.json()
    out = {entry["ticker"].upper(): str(entry["cik_str"]).zfill(10)
           for entry in raw.values()}
    try:
        CACHE_PATH.write_text(json.dumps(out))
    except Exception:  # noqa: BLE001
        pass
    return out


def fetch_8ks_for_cik(cik: str) -> list[dict]:
    """Fetch recent 8-K filings via Atom. Empty list on any failure."""
    try:
        r = requests.get(EDGAR_FEED_URL.format(cik=cik),
                         headers={"User-Agent": USER_AGENT}, timeout=15)
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
    except Exception:  # noqa: BLE001
        return []

    out = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        title = (entry.findtext(f"{ATOM_NS}title") or "").strip()
        updated = (entry.findtext(f"{ATOM_NS}updated") or "").strip()
        link_el = entry.find(f"{ATOM_NS}link")
        href = link_el.get("href") if link_el is not None else ""
        summary_raw = (entry.findtext(f"{ATOM_NS}summary") or "").strip()
        # Strip HTML and sanitize
        summary_clean = sanitize_news(re.sub(r"<[^>]+>", " ", summary_raw))[:300]
        out.append({
            "title": title,
            "filed_at": updated,
            "url": href,
            "summary": summary_clean.strip(),
        })
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", required=True,
                   help="comma-separated tickers, e.g. NVDA,VST,CCJ")
    p.add_argument("--max-per-symbol", type=int, default=5)
    args = p.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    if not symbols:
        sys.exit("no symbols")

    try:
        ticker_map = load_ticker_map()
    except Exception as e:  # noqa: BLE001
        print(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "error": f"ticker map fetch failed: {e}",
            "filings": {},
        }, indent=2))
        sys.exit(0)

    out: dict[str, list[dict]] = {}
    unknown: list[str] = []
    for sym in symbols:
        cik = ticker_map.get(sym)
        if not cik:
            unknown.append(sym)
            continue
        rows = fetch_8ks_for_cik(cik)[: args.max_per_symbol]
        if rows:
            out[sym] = rows

    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "sec_edgar_8k",
        "symbols_requested": symbols,
        "symbols_unknown": unknown,
        "filings": out,
    }, indent=2))


if __name__ == "__main__":
    main()
