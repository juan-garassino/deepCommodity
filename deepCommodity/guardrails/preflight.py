"""The single pre-trade chokepoint. Nothing reaches broker.submit without it.

Fail-closed at every step:
  1. halt   — env DC_HALT / TRADING_MODE=halt / KILL_SWITCH file; unconfirmable -> halt
  2. state  — authoritative broker snapshot; PortfolioUnavailable -> block (no fabrication)
  3. limits — full enhanced check_limits (position incl. existing, sector, gross leverage,
              per-bucket + total daily caps, cash floor, finiteness)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from deepCommodity.execution.portfolio import PortfolioProvider, PortfolioUnavailable
from deepCommodity.guardrails.kill_switch import halt_state
from deepCommodity.guardrails.limits import OrderProposal, PortfolioSnapshot, check_limits


@dataclass
class Decision:
    allow: bool
    reason: str
    code: str   # "ok" | "halt" | "unavailable" | "blocked"
    snapshot: PortfolioSnapshot | None = None


def preflight(
    proposal: OrderProposal,
    provider: PortfolioProvider,
    *,
    strategy: dict | None = None,
    root: Path | None = None,
) -> Decision:
    halted, confirmed, reason = halt_state(root=root)
    if halted or not confirmed:
        return Decision(False, f"HALTED: {reason}", "halt")

    try:
        snapshot = provider.snapshot()
    except PortfolioUnavailable as e:
        return Decision(False, f"BLOCKED: portfolio unavailable ({e})", "unavailable")

    ok, why = check_limits(proposal, snapshot, strategy)
    return Decision(ok, why, "ok" if ok else "blocked", snapshot=snapshot)
