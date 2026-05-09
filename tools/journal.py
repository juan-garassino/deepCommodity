#!/usr/bin/env python
"""Append-only structured writer for RESEARCH-LOG.md and TRADE-LOG.md."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Logs are resolved relative to the *invoking* cwd (not __file__), so cron jobs
# and tests both write to the right place. Routines `cd` into the repo before
# calling tools, and place_order.py subprocess-invokes journal which inherits
# that cwd. The existence check in _append guards against runs from a stray dir.
RESEARCH_LOG = Path("RESEARCH-LOG.md")
TRADE_LOG = Path("TRADE-LOG.md")


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _append(path: Path, header: str, body: str) -> None:
    if not path.exists():
        sys.exit(f"missing log file: {path}")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {_stamp()} — {header}\n\n{body.rstrip()}\n")


def cmd_research(args: argparse.Namespace) -> None:
    _append(RESEARCH_LOG, args.topic, args.body)


def cmd_trade(args: argparse.Namespace) -> None:
    body = (
        f"- symbol: {args.symbol}\n"
        f"- side: {args.side}\n"
        f"- qty: {args.qty}\n"
        f"- status: {args.status}\n"
        f"- mode: {args.mode}\n"
        f"- broker: {args.broker}\n"
        f"- order_id: {args.order_id or '-'}\n"
        f"- fill_price: {args.fill_price or '-'}\n"
        f"- reason: {args.reason}\n"
    )
    header = f"{args.status.upper()} {args.side} {args.qty} {args.symbol}"
    _append(TRADE_LOG, header, body)


def main() -> None:
    p = argparse.ArgumentParser(prog="journal")
    sub = p.add_subparsers(required=True)

    r = sub.add_parser("research")
    r.add_argument("--topic", required=True)
    r.add_argument("--body", required=True)
    r.set_defaults(func=cmd_research)

    t = sub.add_parser("trade")
    t.add_argument("--symbol", required=True)
    t.add_argument("--side", required=True, choices=["buy", "sell"])
    t.add_argument("--qty", required=True)
    t.add_argument("--status", required=True,
                   choices=["placed", "filled", "rejected", "skipped", "blocked"])
    t.add_argument("--mode", default="paper")
    t.add_argument("--broker", default="-")
    t.add_argument("--order-id", default="")
    t.add_argument("--fill-price", default="")
    t.add_argument("--reason", default="")
    t.set_defaults(func=cmd_trade)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
