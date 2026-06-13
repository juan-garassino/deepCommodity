"""Pure helpers for valuing crypto exchange balances in USD (no network).

Kept separate from the ccxt adapter so the audit-critical math (B5) is unit-tested
without a live client.
"""
from __future__ import annotations

# Treated as 1 USD. (USD/USDT/USDC peg assumed; good enough for sizing gates.)
STABLES = {"USDT", "USDC", "USD", "BUSD", "DAI", "TUSD", "FDUSD"}
# Stables that count as deployable cash for the cash-floor check.
CASH_STABLES = {"USDT", "USD", "USDC"}


def _price_usd(asset: str, tickers: dict) -> float | None:
    for quote in ("USDT", "USD", "USDC"):
        t = tickers.get(f"{asset}/{quote}")
        if t and t.get("last"):
            return float(t["last"])
    return None


def value_crypto_balances(
    totals: dict[str, float],
    free: dict[str, float],
    tickers: dict[str, dict],
) -> tuple[float, dict[str, float], float]:
    """Return (nav_usd, positions_usd, cash_usd).

    - stables count 1:1 toward NAV; CASH_STABLES also count toward cash.
    - non-stable assets are valued via tickers; unpriceable holdings are skipped
      (understates NAV, which is conservative for the per-position cap).
    """
    nav = 0.0
    cash = 0.0
    positions: dict[str, float] = {}
    for asset, qty in totals.items():
        try:
            q = float(qty)
        except (TypeError, ValueError):
            continue
        if q <= 0:
            continue
        upper = asset.upper()
        if upper in STABLES:
            nav += q
            if upper in CASH_STABLES:
                cash += float(free.get(asset, q))
            continue
        px = _price_usd(upper, tickers)
        if px is None:
            continue
        usd = q * px
        nav += usd
        positions[asset] = positions.get(asset, 0.0) + usd
    return nav, positions, cash
