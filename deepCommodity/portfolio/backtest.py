"""Portfolio backtester: signed price weights + delta-neutral carry weights ->
equity curve and risk-adjusted metrics, with honest costs.

Causality: weights decided at t-1 earn price return / funding at t. Each step a
risk multiplier (vol-target ∧ drawdown-ladder) scales the book; per-name + gross
caps are then enforced. Funding earned = carry_weight × funding (carry shorts the
high-funding perp delta-neutral, so positive funding is income). Turnover is
charged taker_bps; gross > 1× is charged borrow_bps_ann financing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from deepCommodity.portfolio import risk
from deepCommodity.portfolio.portfolios import Costs, PortfolioCfg

TRADING_DAYS = 365
DD_WINDOW = 90        # the ladder de-risks on the trailing-90d drawdown, then re-risks
                      # (an all-time peak would make a halt absorbing — zero exposure
                      #  can never recover). The REPORTED max_dd is still all-time.


def run(price_w: pd.DataFrame, carry_w: pd.DataFrame, rets: pd.DataFrame,
        funding: pd.DataFrame, cfg: PortfolioCfg, costs: Costs) -> dict:
    idx = rets.index
    cols = rets.columns
    pw = price_w.reindex(idx).reindex(columns=cols).fillna(0.0).to_numpy()
    cw = carry_w.reindex(idx).reindex(columns=cols).fillna(0.0).to_numpy()
    R = rets.fillna(0.0).to_numpy()
    F = funding.reindex(idx).reindex(columns=cols).fillna(0.0).to_numpy()

    equity = 1.0
    prev_p = np.zeros(len(cols)); prev_c = np.zeros(len(cols))
    rets_hist: list[float] = []
    curve, gross_log, net_log = [], [], []
    carry_pnl_sum = 0.0

    for t in range(1, len(idx)):
        peak = max(max(curve[-DD_WINDOW:], default=equity), equity)   # trailing peak
        dd = equity / peak - 1.0
        m_vol = risk.vol_scale(np.array(rets_hist[-20:]), cfg.vol_target, cfg.max_gross)
        m_dd = risk.dd_multiplier(dd, cfg.de_lever_dd, cfg.halt_dd)
        mult = m_vol * m_dd

        p = risk.cap_per_name(pw[t - 1] * mult, cfg.max_name)
        c = cw[t - 1] * mult
        p, c = risk.cap_gross(p, c, cfg.max_gross)

        price_pnl = float(np.dot(p, R[t]))
        carry_pnl = float(np.dot(c, F[t]))            # earn funding on carry names
        turnover = float(np.abs(p - prev_p).sum() + np.abs(c - prev_c).sum())
        cost = turnover * costs.taker_bps / 1e4
        gross = float(np.abs(p).sum() + np.abs(c).sum())
        financing = max(0.0, gross - 1.0) * costs.borrow_bps_ann / 1e4 / TRADING_DAYS
        ret = price_pnl + carry_pnl - cost - financing

        equity *= (1.0 + ret)
        rets_hist.append(ret); carry_pnl_sum += carry_pnl
        curve.append(equity); gross_log.append(gross); net_log.append(float(p.sum()))
        prev_p, prev_c = p, c

    return _metrics(np.array(rets_hist), np.array(curve), np.array(gross_log),
                    np.array(net_log), carry_pnl_sum, cfg.name)


def _metrics(rets: np.ndarray, curve: np.ndarray, gross: np.ndarray, net: np.ndarray,
             carry_pnl: float, name: str) -> dict:
    if len(rets) < 30:
        return {"portfolio": name, "error": "too few steps"}
    ann = TRADING_DAYS
    mu, sd = rets.mean(), rets.std()
    downside = rets[rets < 0].std()
    peak = np.maximum.accumulate(curve)
    max_dd = float((curve / peak - 1.0).min())
    cagr = float(curve[-1] ** (ann / len(rets)) - 1.0)
    sharpe = float(mu / (sd + 1e-12) * np.sqrt(ann))
    sortino = float(mu / (downside + 1e-12) * np.sqrt(ann))
    calmar = float(cagr / abs(max_dd)) if max_dd < 0 else 0.0
    return {
        "portfolio": name,
        "cagr": round(cagr, 4), "ann_vol": round(sd * np.sqrt(ann), 4),
        "sharpe": round(sharpe, 2), "sortino": round(sortino, 2),
        "max_drawdown": round(max_dd, 4), "calmar": round(calmar, 2),
        "avg_gross": round(float(gross.mean()), 2), "avg_net": round(float(net.mean()), 3),
        "carry_pnl_total": round(carry_pnl, 4), "n_days": int(len(rets)),
    }
