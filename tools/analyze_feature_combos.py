#!/usr/bin/env python
"""Find the best feature combination for forward-return prediction.

Cheap linear probe (no model training): builds an enriched candidate feature set
(macro + transforms + multi-horizon momentum + volatility), pools (date, asset)
samples, and scores feature COMBINATIONS by walk-forward out-of-sample IC using
ridge regression. Greedy forward selection finds the best combo per horizon, so
the eventual big transformer trains on the winning signals rather than everything.

Leakage-safe: features are point-in-time (macro.csv is already publication-lag
shifted; price features are trailing), walk-forward folds are strictly time-ordered.
numpy-only ridge — no sklearn dependency.

Writes data/reports/feature_combos_<date>.md and prints the ranked winners.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.analyze_contextual_data import _load_bars  # noqa: E402
from tools.fetch_macro_features import MACRO_FEATURE_COLS  # noqa: E402


def _build_panel(bars: dict, macro: pd.DataFrame, horizons: dict[str, int]) -> pd.DataFrame:
    """Pooled (date, asset) rows: candidate features + forward-return targets.

    Mixes the slow macro panel with 'unusual' quant-alpha signals derivable from
    the bars (all trailing/causal): short-term reversal, volatility regime, volume
    surge, mean-reversion vs MA, drawdown-from-ATH, momentum acceleration, weekly
    seasonality, and cross-sectional relative strength vs BTC.
    """
    btc_close = bars["BTC"]["close"].astype(float) if "BTC" in bars else None
    rows = []
    for sym, df in bars.items():
        close = df["close"].astype(float)
        ret1 = close.pct_change()
        m = macro.reindex(df.index).ffill()
        feat = pd.DataFrame(index=df.index)
        # --- macro (drop the degraded totalcap) ---
        for c in MACRO_FEATURE_COLS:
            if c != "totalcap_chg4w":
                feat[c] = m[c]
        feat["m2_accel"] = m["m2_yoy"].diff(28)               # change in M2 growth
        feat["netliq_x_dom"] = m["netliq_z"] * m["btc_dom"]    # macro interaction
        # --- usual: momentum at horizons ---
        for h in (5, 10, 20):
            feat[f"mom_{h}"] = close / close.shift(h) - 1.0
        # --- unusual / quant-alpha signals (causal) ---
        feat["reversal_3"] = -(close / close.shift(3) - 1.0)              # short-term reversal
        feat["vol_ratio"] = ret1.rolling(5).std() / (ret1.rolling(20).std() + 1e-9)  # vol regime
        feat["vol_of_vol"] = ret1.rolling(20).std().pct_change(5)         # vol-of-vol
        feat["volume_z"] = ((df["volume"] - df["volume"].rolling(20).mean())
                            / (df["volume"].rolling(20).std() + 1e-9))     # volume surge
        feat["dist_ma50"] = close / close.rolling(50).mean() - 1.0        # mean-reversion vs MA
        feat["drawdown"] = close / close.cummax() - 1.0                   # distance from ATH
        feat["accel"] = ret1.rolling(5).mean() - ret1.rolling(20).mean()  # momentum acceleration
        dow = df.index.dayofweek.to_numpy()
        feat["dow_sin"] = np.sin(2 * np.pi * dow / 7)                     # weekly seasonality
        feat["dow_cos"] = np.cos(2 * np.pi * dow / 7)
        if btc_close is not None and sym != "BTC":                       # cross-sectional rel. strength
            btc_aligned = btc_close.reindex(df.index).ffill()
            feat["rel_btc_10"] = (close / close.shift(10) - 1.0) - (btc_aligned / btc_aligned.shift(10) - 1.0)
        else:
            feat["rel_btc_10"] = 0.0
        # --- targets ---
        for name, h in horizons.items():
            feat[f"y_{name}"] = close.shift(-h) / close - 1.0
        feat["asset"] = sym
        rows.append(feat)
    panel = pd.concat(rows).dropna()
    panel["date"] = panel.index
    return panel.reset_index(drop=True)


def _ridge_oos_ic(X: np.ndarray, y: np.ndarray, dates: np.ndarray, folds: int, lam: float) -> float:
    """Walk-forward (expanding) out-of-sample IC of a ridge fit on feature matrix X."""
    order = np.argsort(dates, kind="stable")
    X, y = X[order], y[order]
    n = len(y)
    edges = [int(n * k / (folds + 1)) for k in range(1, folds + 2)]
    preds, actual = [], []
    for i in range(folds):
        tr_end, te_end = edges[i], edges[i + 1]
        Xtr, ytr = X[:tr_end], y[:tr_end]
        Xte, yte = X[tr_end:te_end], y[tr_end:te_end]
        if len(Xtr) < 50 or len(Xte) < 20:
            continue
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
        Xtr_s, Xte_s = (Xtr - mu) / sd, (Xte - mu) / sd
        Xtr_b = np.hstack([Xtr_s, np.ones((len(Xtr_s), 1))])
        Xte_b = np.hstack([Xte_s, np.ones((len(Xte_s), 1))])
        A = Xtr_b.T @ Xtr_b + lam * np.eye(Xtr_b.shape[1])
        w = np.linalg.solve(A, Xtr_b.T @ ytr)
        preds.append(Xte_b @ w); actual.append(yte)
    if not preds:
        return 0.0
    p, a = np.concatenate(preds), np.concatenate(actual)
    if np.std(p) == 0 or np.std(a) == 0:
        return 0.0
    return float(np.corrcoef(p, a)[0, 1])


def greedy_combo(panel: pd.DataFrame, feats: list[str], target: str, folds: int, lam: float) -> dict:
    dates = panel["date"].values.astype("datetime64[ns]").astype("int64")
    y = panel[target].to_numpy()
    singles = sorted(((f, _ridge_oos_ic(panel[[f]].to_numpy(), y, dates, folds, lam)) for f in feats),
                     key=lambda kv: -abs(kv[1]))
    chosen, best_ic = [], 0.0
    pool = [f for f, _ in singles]
    while pool:
        scored = [(f, _ridge_oos_ic(panel[chosen + [f]].to_numpy(), y, dates, folds, lam)) for f in pool]
        f_best, ic_best = max(scored, key=lambda kv: abs(kv[1]))
        if abs(ic_best) <= abs(best_ic) + 0.002:   # stop when no real improvement
            break
        chosen.append(f_best); best_ic = ic_best; pool.remove(f_best)
    return {"singles_top": [(f, round(ic, 4)) for f, ic in singles[:6]],
            "best_combo": chosen, "best_combo_ic": round(best_ic, 4)}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", default="BTC,ETH,SOL")
    p.add_argument("--bars-dir", default=str(ROOT / "data" / "bars"))
    p.add_argument("--macro", default=str(ROOT / "data" / "macro" / "features.csv"))
    p.add_argument("--folds", type=int, default=5)
    p.add_argument("--lam", type=float, default=10.0)
    p.add_argument("--report-dir", default=str(ROOT / "data" / "reports"))
    args = p.parse_args()

    macro = pd.read_csv(args.macro, index_col="date", parse_dates=True)[MACRO_FEATURE_COLS]
    macro.index = macro.index.normalize()
    syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    bars = {s: _load_bars(Path(args.bars_dir) / f"{s}.csv") for s in syms}
    bars = {s: d for s, d in bars.items() if d is not None}

    horizons = {"daily": 2, "weekly": 10, "biweekly": 20}
    panel = _build_panel(bars, macro, horizons)
    feats = [c for c in panel.columns if not c.startswith("y_") and c not in ("asset", "date")]

    # Regime-neutral targets: subtract the per-date cross-sectional mean forward return,
    # so the metric measures relative-strength alpha, not the common bull/bear drift.
    for name in horizons:
        panel[f"yn_{name}"] = panel[f"y_{name}"] - panel.groupby("date")[f"y_{name}"].transform("mean")

    dates = panel["date"].values.astype("datetime64[ns]").astype("int64")
    out = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "n_samples": int(len(panel)), "target": "cross-sectionally demeaned forward return",
           "candidate_features": feats, "per_horizon": {}}
    for name in horizons:
        res = greedy_combo(panel, feats, f"yn_{name}", args.folds, args.lam)
        mom_ic = _ridge_oos_ic(panel[["mom_10"]].to_numpy(), panel[f"yn_{name}"].to_numpy(),
                               dates, args.folds, args.lam)
        res["momentum_baseline_ic"] = round(mom_ic, 4)
        res["combo_beats_momentum"] = abs(res["best_combo_ic"]) > abs(mom_ic)
        out["per_horizon"][name] = res

    rep_dir = Path(args.report_dir); rep_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    (rep_dir / f"feature_combos_{stamp}.md").write_text(
        f"# Best feature combo ({stamp})\n\n```json\n{json.dumps(out, indent=2)}\n```\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
