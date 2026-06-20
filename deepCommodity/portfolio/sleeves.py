"""Sleeve weight constructors -> date×symbol weight panels.

Two weight kinds:
  * price-bearing weights (XS + DIR): exposed to price returns. Signed.
  * carry weights (CARRY): delta-neutral (short perp / long spot), price-neutral,
    earn funding on the selected names. Non-negative harvest size.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def xs_weights(score: pd.DataFrame, frac: float = 0.3) -> pd.DataFrame:
    """Dollar-neutral L/S: long top `frac`, short bottom `frac`, gross 1, net 0."""
    w = pd.DataFrame(0.0, index=score.index, columns=score.columns)
    for t, row in score.iterrows():
        r = row.dropna()
        if len(r) < 4:
            continue
        k = max(1, int(len(r) * frac))
        ranked = r.sort_values()
        shorts, longs = ranked.index[:k], ranked.index[-k:]
        w.loc[t, longs] = 0.5 / len(longs)
        w.loc[t, shorts] = -0.5 / len(shorts)
    return w


def dir_weights(regime: pd.Series, columns, beta_basket=("BTC", "ETH"),
                strength: float = 1.0) -> pd.DataFrame:
    """Net long/short crypto beta sized by regime sign (equal-weight basket)."""
    w = pd.DataFrame(0.0, index=regime.index, columns=list(columns))
    basket = [s for s in beta_basket if s in w.columns] or list(w.columns)[:2]
    per = strength / max(1, len(basket))
    for s in basket:
        w[s] = regime.astype(float) * per           # +regime long basket, -regime short
    return w


def carry_weights(score: pd.DataFrame, frac: float = 0.3) -> pd.DataFrame:
    """Select top-`frac` positive-funding names to harvest (delta-neutral). Sums to 1."""
    w = pd.DataFrame(0.0, index=score.index, columns=score.columns)
    for t, row in score.iterrows():
        pos = row[row > 0].dropna()
        if pos.empty:
            continue
        k = max(1, int(len(row.dropna()) * frac))
        top = pos.sort_values().index[-k:]
        w.loc[t, top] = 1.0 / len(top)
    return w
