from dataclasses import dataclass

# Hardcoded ceilings — TRADING-STRATEGY.md may set tighter values, never looser.
HARD_LIMITS = {
    "max_single_position_pct": 0.05,
    "max_sector_concentration_pct": 0.30,
    "max_new_positions_per_day": 3,
    "max_gross_leverage": 1.0,
    "min_cash_floor_pct": 0.10,
}


@dataclass
class OrderProposal:
    symbol: str
    side: str            # "buy" | "sell"
    qty: float
    notional_usd: float
    sector: str | None = None


@dataclass
class PortfolioSnapshot:
    nav_usd: float
    cash_usd: float
    positions: dict[str, float]              # symbol -> notional_usd
    sector_notional: dict[str, float]        # sector -> notional_usd
    new_positions_today: int


def check_limits(
    proposal: OrderProposal,
    portfolio: PortfolioSnapshot,
    strategy: dict | None = None,
) -> tuple[bool, str]:
    """Return (ok, reason). False reason is the human-readable block message."""
    s = strategy or {}
    nav = portfolio.nav_usd
    if nav <= 0:
        return False, "BLOCKED: NAV is zero or negative"

    if proposal.side == "buy":
        max_pos = min(
            HARD_LIMITS["max_single_position_pct"],
            s.get("max_single_position_pct", HARD_LIMITS["max_single_position_pct"]),
        )
        if proposal.notional_usd / nav > max_pos:
            return False, f"BLOCKED: position {proposal.notional_usd/nav:.2%} > cap {max_pos:.2%}"

        max_sector = min(
            HARD_LIMITS["max_sector_concentration_pct"],
            s.get("max_sector_concentration_pct", HARD_LIMITS["max_sector_concentration_pct"]),
        )
        if proposal.sector:
            current = portfolio.sector_notional.get(proposal.sector, 0.0)
            if (current + proposal.notional_usd) / nav > max_sector:
                return False, f"BLOCKED: sector {proposal.sector} would exceed {max_sector:.2%}"

        max_new = min(
            HARD_LIMITS["max_new_positions_per_day"],
            s.get("max_new_positions_per_day", HARD_LIMITS["max_new_positions_per_day"]),
        )
        if proposal.symbol not in portfolio.positions and portfolio.new_positions_today >= max_new:
            return False, f"BLOCKED: already opened {max_new} new positions today"

        cash_after = portfolio.cash_usd - proposal.notional_usd
        floor = HARD_LIMITS["min_cash_floor_pct"] * nav
        if cash_after < floor:
            return False, f"BLOCKED: would breach cash floor ({cash_after:.0f} < {floor:.0f})"

    return True, "OK"
