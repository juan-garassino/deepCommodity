#!/usr/bin/env python
"""Pre-trade gate. Returns OK or BLOCKED: <reason>; non-zero exit on block."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.guardrails.kill_switch import is_armed  # noqa: E402
from deepCommodity.guardrails.limits import (  # noqa: E402
    OrderProposal,
    PortfolioSnapshot,
    check_limits,
)


def _portfolio_for(asset_class: str) -> PortfolioSnapshot:
    """Best-effort live portfolio. Falls back to a 10k paper portfolio if broker unavailable."""
    try:
        from deepCommodity.execution import get_broker
        b = get_broker(asset_class)  # type: ignore[arg-type]
        nav = b.portfolio_nav()
        positions = b.positions()
        # heuristic cash: NAV minus sum of positions (broker-specific in reality)
        cash = max(0.0, nav - sum(positions.values()))
        return PortfolioSnapshot(
            nav_usd=nav, cash_usd=cash, positions=positions,
            sector_notional={}, new_positions_today=0,
        )
    except Exception:
        return PortfolioSnapshot(
            nav_usd=10_000.0, cash_usd=10_000.0, positions={},
            sector_notional={}, new_positions_today=0,
        )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", required=True)
    p.add_argument("--side", required=True, choices=["buy", "sell"])
    p.add_argument("--qty", required=True, type=float)
    p.add_argument("--price", required=True, type=float, help="reference price USD")
    p.add_argument("--asset-class", required=True, choices=["crypto", "equity"])
    p.add_argument("--sector", default=None)
    args = p.parse_args()

    if is_armed():
        print("BLOCKED: KILL_SWITCH armed")
        sys.exit(2)

    proposal = OrderProposal(
        symbol=args.symbol, side=args.side, qty=args.qty,
        notional_usd=args.qty * args.price, sector=args.sector,
    )
    portfolio = _portfolio_for(args.asset_class)
    ok, reason = check_limits(proposal, portfolio)
    print(reason)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
