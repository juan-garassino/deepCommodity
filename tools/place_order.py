#!/usr/bin/env python
"""Submit an order to Binance (crypto) or Alpaca (equity).

Hard gates, in order:
  1. KILL_SWITCH file present -> abort.
  2. risk_check passes (re-runs in-process, not via subprocess).
  3. If TRADING_MODE=live, --confirm-live flag is required.
Always journals the outcome to TRADE-LOG.md.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.execution.broker import OrderRequest, get_broker  # noqa: E402
from deepCommodity.guardrails.kill_switch import is_armed  # noqa: E402
from deepCommodity.guardrails.limits import (  # noqa: E402
    OrderProposal,
    check_limits,
)


def _journal(args, status: str, result: dict, reason: str) -> None:
    cmd = [
        sys.executable, str(ROOT / "tools" / "journal.py"), "trade",
        "--symbol", args.symbol, "--side", args.side, "--qty", str(args.qty),
        "--status", status, "--mode", os.getenv("TRADING_MODE", "paper"),
        "--broker", result.get("broker", "-"),
        "--order-id", str(result.get("order_id") or ""),
        "--fill-price", str(result.get("fill_price") or ""),
        "--reason", reason,
    ]
    subprocess.run(cmd, check=False)
    _telegram(args, status, result, reason)


def _telegram(args, status: str, result: dict, reason: str) -> None:
    """Best-effort Telegram ping. Silent if env not configured."""
    severity = {"filled": "ok", "placed": "info", "rejected": "error",
                "blocked": "warn", "skipped": "info"}.get(status, "info")
    fill = result.get("fill_price")
    body = (f"{status.upper()} {args.side} {args.qty} {args.symbol} "
            f"@ {fill or '-'}  ({os.getenv('TRADING_MODE', 'paper')})\n"
            f"reason: {reason}")
    subprocess.run([
        sys.executable, str(ROOT / "tools" / "notify_telegram.py"),
        "--topic", "trade", "--severity", severity, "--message", body, "--quiet",
    ], check=False)


def _portfolio(asset_class: str):
    from deepCommodity.guardrails.limits import PortfolioSnapshot
    try:
        b = get_broker(asset_class)
        nav = b.portfolio_nav()
        positions = b.positions()
        cash = max(0.0, nav - sum(positions.values()))
        return PortfolioSnapshot(nav_usd=nav, cash_usd=cash, positions=positions,
                                 sector_notional={}, new_positions_today=0)
    except Exception:
        return PortfolioSnapshot(nav_usd=10_000.0, cash_usd=10_000.0,
                                 positions={}, sector_notional={},
                                 new_positions_today=0)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", required=True)
    p.add_argument("--side", required=True, choices=["buy", "sell"])
    p.add_argument("--qty", required=True, type=float)
    p.add_argument("--price", type=float, default=0.0,
                   help="reference price for risk check (USD); required for buy")
    p.add_argument("--asset-class", required=True, choices=["crypto", "equity"])
    p.add_argument("--type", default="market", choices=["market", "limit"])
    p.add_argument("--limit-price", type=float, default=None)
    p.add_argument("--stop-loss-pct", type=float, default=None)
    p.add_argument("--take-profit-pct", type=float, default=None)
    p.add_argument("--sector", default=None)
    p.add_argument("--reason", required=True, help="why this trade (free text, journaled)")
    p.add_argument("--confirm-live", action="store_true",
                   help="required when TRADING_MODE=live")
    args = p.parse_args()

    mode = os.getenv("TRADING_MODE", "paper").lower()

    # Gate 1: kill switch
    if is_armed():
        print("BLOCKED: KILL_SWITCH armed", file=sys.stderr)
        _journal(args, "blocked", {}, "KILL_SWITCH armed")
        sys.exit(2)

    # Gate 2: live confirmation
    if mode == "live" and not args.confirm_live:
        print("BLOCKED: TRADING_MODE=live requires --confirm-live", file=sys.stderr)
        _journal(args, "blocked", {}, "live mode without --confirm-live")
        sys.exit(3)
    if mode == "live":
        print("=" * 60, file=sys.stderr)
        print(f"LIVE ORDER: {args.side} {args.qty} {args.symbol} on {args.asset_class}",
              file=sys.stderr)
        print("=" * 60, file=sys.stderr)

    # Gate 3: risk check
    proposal = OrderProposal(
        symbol=args.symbol, side=args.side, qty=args.qty,
        notional_usd=args.qty * (args.price or args.limit_price or 0.0),
        sector=args.sector,
    )
    ok, reason = check_limits(proposal, _portfolio(args.asset_class))
    if not ok:
        print(reason, file=sys.stderr)
        _journal(args, "blocked", {}, reason)
        sys.exit(1)

    # Submit
    broker = get_broker(args.asset_class)
    req = OrderRequest(
        symbol=args.symbol, side=args.side, qty=args.qty,
        asset_class=args.asset_class, type=args.type,
        limit_price=args.limit_price,
        stop_loss_pct=args.stop_loss_pct, take_profit_pct=args.take_profit_pct,
    )
    result = broker.submit(req)

    payload = {
        "ok": result.ok, "broker": result.broker, "mode": result.mode,
        "symbol": result.symbol, "side": result.side, "qty": result.qty,
        "fill_price": result.fill_price, "order_id": result.order_id,
        "error": result.error,
    }
    print(json.dumps(payload, indent=2))
    _journal(args, "filled" if result.ok else "rejected", payload,
             args.reason + (f" | error={result.error}" if not result.ok else ""))
    sys.exit(0 if result.ok else 4)


if __name__ == "__main__":
    main()
