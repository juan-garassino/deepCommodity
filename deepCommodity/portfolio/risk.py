"""Risk overlay: vol targeting, leverage caps, and the graduated drawdown ladder.

All functions are causal (use only info up to the current step). The backtester
calls vol_scale + dd_multiplier each step to get a time-varying exposure multiplier.
"""
from __future__ import annotations

import numpy as np

TRADING_DAYS = 365   # crypto trades 24/7


def vol_scale(recent_rets: np.ndarray, target_ann_vol: float, max_mult: float) -> float:
    """Scalar so the book's realized vol tracks the target. Clipped to [0, max_mult]."""
    if len(recent_rets) < 10:
        return 1.0
    rv = np.std(recent_rets) * np.sqrt(TRADING_DAYS)
    if rv <= 1e-9:
        return max_mult
    return float(np.clip(target_ann_vol / rv, 0.0, max_mult))


def dd_multiplier(drawdown: float, de_lever_dd: float, halt_dd: float) -> float:
    """Exposure multiplier from the current drawdown (drawdown <= 0).

    1.0 until de_lever_dd, then linearly ramp to 0 at halt_dd, 0 beyond. The
    graduated ladder replaces a binary kill-switch (which only fires at the bottom).
    """
    dd = min(0.0, drawdown)
    if dd >= de_lever_dd:
        return 1.0
    if dd <= halt_dd:
        return 0.0
    return float((dd - halt_dd) / (de_lever_dd - halt_dd))   # in (0,1)


def cap_gross(price_w: np.ndarray, carry_w: np.ndarray, max_gross: float) -> tuple:
    """Scale price+carry weights so total gross <= max_gross."""
    gross = np.abs(price_w).sum() + np.abs(carry_w).sum()
    if gross <= max_gross or gross <= 1e-9:
        return price_w, carry_w
    s = max_gross / gross
    return price_w * s, carry_w * s


def cap_per_name(price_w: np.ndarray, max_name: float) -> np.ndarray:
    return np.clip(price_w, -max_name, max_name)
