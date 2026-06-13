from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime

# Hardcoded ceilings — TRADING-STRATEGY.md may set tighter values, never looser.
HARD_LIMITS = {
    "max_single_position_pct": 0.05,
    "max_sector_concentration_pct": 0.30,
    "max_new_positions_per_day": 3,
    "max_gross_leverage": 1.0,
    "min_cash_floor_pct": 0.10,
}

# Per-bucket daily new-position caps (in addition to the total cap above).
# anchor 1 / theme 2 / gem 1 == 4 possible, total cap 3 binds first.
BUCKET_DAILY_CAPS = {
    "anchor": 1,
    "theme": 2,
    "gem": 1,
}


@dataclass
class OrderProposal:
    symbol: str
    side: str            # "buy" | "sell"
    qty: float
    notional_usd: float
    sector: str | None = None
    bucket: str | None = None   # "anchor" | "theme" | "gem"


@dataclass
class PortfolioSnapshot:
    nav_usd: float
    cash_usd: float
    positions: dict[str, float]               # symbol -> notional_usd
    sector_notional: dict[str, float]         # sector -> notional_usd
    new_positions_today: dict[str, int] = field(default_factory=dict)  # bucket -> count
    as_of: datetime | None = None
    source: str = ""


def _finite_positive(x: float) -> bool:
    try:
        return math.isfinite(float(x)) and float(x) > 0
    except (TypeError, ValueError):
        return False


def check_limits(
    proposal: OrderProposal,
    portfolio: PortfolioSnapshot,
    strategy: dict | None = None,
) -> tuple[bool, str]:
    """Return (ok, reason). False reason is the human-readable block message.

    Fail-closed: invalid inputs (non-finite / non-positive qty or notional, bad NAV)
    block rather than slip through numeric comparisons.
    """
    s = strategy or {}

    # ---- input validation --------------------------------------------------
    if not _finite_positive(proposal.qty):
        return False, f"BLOCKED: invalid qty {proposal.qty!r} (must be finite > 0)"

    nav = portfolio.nav_usd
    if not (isinstance(nav, (int, float)) and math.isfinite(nav)) or nav <= 0:
        return False, "BLOCKED: NAV is zero or negative"

    if proposal.side == "buy":
        # notional must be a real positive number for any sizing-based gate
        if not _finite_positive(proposal.notional_usd):
            return False, f"BLOCKED: invalid notional {proposal.notional_usd!r} (must be finite > 0)"

        # per-position cap — counts the EXISTING holding of the same symbol (no pyramiding)
        max_pos = min(
            HARD_LIMITS["max_single_position_pct"],
            s.get("max_single_position_pct", HARD_LIMITS["max_single_position_pct"]),
        )
        existing = portfolio.positions.get(proposal.symbol, 0.0)
        combined = existing + proposal.notional_usd
        if combined / nav > max_pos:
            return False, f"BLOCKED: position {combined/nav:.2%} > cap {max_pos:.2%}"

        # sector concentration
        max_sector = min(
            HARD_LIMITS["max_sector_concentration_pct"],
            s.get("max_sector_concentration_pct", HARD_LIMITS["max_sector_concentration_pct"]),
        )
        if proposal.sector:
            current = portfolio.sector_notional.get(proposal.sector, 0.0)
            if (current + proposal.notional_usd) / nav > max_sector:
                return False, f"BLOCKED: sector {proposal.sector} would exceed {max_sector:.2%}"

        # gross leverage — total exposure must stay within the ceiling
        max_lev = min(
            HARD_LIMITS["max_gross_leverage"],
            s.get("max_gross_leverage", HARD_LIMITS["max_gross_leverage"]),
        )
        gross = (sum(portfolio.positions.values()) + proposal.notional_usd) / nav
        if gross > max_lev:
            return False, f"BLOCKED: gross leverage {gross:.2f}x > {max_lev:.2f}x"

        # daily new-position caps (total + per-bucket), only for a genuinely new symbol
        if proposal.symbol not in portfolio.positions:
            today = portfolio.new_positions_today or {}
            total_today = sum(today.values())
            max_new = min(
                HARD_LIMITS["max_new_positions_per_day"],
                s.get("max_new_positions_per_day", HARD_LIMITS["max_new_positions_per_day"]),
            )
            if total_today >= max_new:
                return False, f"BLOCKED: already opened {max_new} new positions today"
            bucket = proposal.bucket
            if bucket:
                cap = BUCKET_DAILY_CAPS.get(bucket)
                if cap is not None and today.get(bucket, 0) >= cap:
                    return False, f"BLOCKED: {bucket} bucket daily cap {cap} reached"

        # cash floor
        cash_after = portfolio.cash_usd - proposal.notional_usd
        floor = HARD_LIMITS["min_cash_floor_pct"] * nav
        if cash_after < floor:
            return False, f"BLOCKED: would breach cash floor ({cash_after:.0f} < {floor:.0f})"

    return True, "OK"
