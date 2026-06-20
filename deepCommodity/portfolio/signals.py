"""Cross-sectional + carry signals (all causal/trailing).

xs_score : cross-sectional relative strength — the measured edge (rel-strength +
           a vol-regime tilt). Higher = expected to outperform the cross-section.
carry_score : trailing-mean funding; higher = more carry to harvest (short the perp).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def xs_score(prices: pd.DataFrame, mom_lb: int = 10, vol_lb: int = 20) -> pd.DataFrame:
    """Cross-sectional momentum, vol-scaled, demeaned across assets per date."""
    rets = prices.pct_change()
    mom = prices / prices.shift(mom_lb) - 1.0
    vol = rets.rolling(vol_lb).std()
    risk_adj = mom / (vol + 1e-9)                      # vol-regime tilt: favor steadier movers
    # cross-sectional z-score per date (relative strength)
    z = risk_adj.sub(risk_adj.mean(axis=1), axis=0).div(risk_adj.std(axis=1) + 1e-9, axis=0)
    return z.replace([np.inf, -np.inf], 0.0).fillna(0.0)


def carry_score(funding: pd.DataFrame, lb: int = 7) -> pd.DataFrame:
    """Trailing-mean daily funding (already lagged in the loader)."""
    return funding.rolling(lb).mean().fillna(0.0)
