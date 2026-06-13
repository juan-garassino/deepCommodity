#!/usr/bin/env python
"""Pre-trade gate. Thin wrapper over the single preflight() chokepoint.

Exit: 0 = OK | 1 = blocked or portfolio unavailable | 2 = halt.
Fail-closed: a broker that can't report state blocks the trade (never assumes a
clean book). place_order re-runs the same gate before submitting.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity import config  # noqa: E402
from deepCommodity.execution.portfolio import make_provider  # noqa: E402
from deepCommodity.guardrails.limits import OrderProposal  # noqa: E402
from deepCommodity.guardrails.preflight import preflight  # noqa: E402
from deepCommodity.universe import Universe, classify_symbol  # noqa: E402


def evaluate(*, symbol, side, qty, price, asset_class, sector=None,
             provider=None, home: Path | None = None) -> tuple[int, str]:
    symbol = symbol.strip().upper()  # canonical key (match broker position keys)
    universe = Universe.load()
    if provider is None:
        try:
            provider, _ = make_provider(asset_class, home=home, universe=universe)
        except Exception as e:  # noqa: BLE001
            return 1, f"BLOCKED: portfolio unavailable ({e})"
    bucket, derived_sector = classify_symbol(universe, symbol)
    proposal = OrderProposal(
        symbol=symbol, side=side, qty=qty, notional_usd=qty * price,
        sector=sector or derived_sector, bucket=bucket,
    )
    decision = preflight(proposal, provider, root=config.dc_home(home))
    if decision.allow:
        return 0, decision.reason
    return (2 if decision.code == "halt" else 1), decision.reason


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", required=True)
    p.add_argument("--side", required=True, choices=["buy", "sell"])
    p.add_argument("--qty", required=True, type=float)
    p.add_argument("--price", required=True, type=float, help="reference price USD")
    p.add_argument("--asset-class", required=True, choices=["crypto", "equity"])
    p.add_argument("--sector", default=None)
    args = p.parse_args()
    code, reason = evaluate(
        symbol=args.symbol, side=args.side, qty=args.qty, price=args.price,
        asset_class=args.asset_class, sector=args.sector,
    )
    print(reason)
    sys.exit(code)


if __name__ == "__main__":
    main()
