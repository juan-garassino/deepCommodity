#!/usr/bin/env python
"""Data-quality audit + macro-signal analysis for the contextual forecaster.

Answers the pre-training question: is there exploitable signal in the macro->crypto
relationship, and is the data clean enough to model? No model training here.

  1. DATA QUALITY  — per-asset bar coverage, gaps, dupes, zero-volume; per-macro-
     feature coverage, NaN, variance (flags degraded/constant features).
  2. SIGNAL        — Information Coefficient (Pearson corr) of each macro feature
     vs forward returns (weekly/daily), pooled across assets; the price-momentum
     baseline IC; regime-bucketed forward returns + win rates (does EXPANDING
     actually precede higher returns?); baseline directional accuracy.

Writes data/reports/contextual_data_analysis_<date>.md and prints a summary.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.model.contextual_transformer import regime_readout  # noqa: E402
from tools.fetch_macro_features import MACRO_FEATURE_COLS  # noqa: E402


def _load_bars(csv: Path) -> pd.DataFrame | None:
    if not csv.exists():
        return None
    df = pd.read_csv(csv)
    if np.issubdtype(df["ts"].dtype, np.number):
        df["date"] = pd.to_datetime(df["ts"], unit="ms").dt.normalize()
    else:
        df["date"] = pd.to_datetime(df["ts"], utc=True).dt.tz_localize(None).dt.normalize()
    return df.set_index("date")


def _ic(x: np.ndarray, y: np.ndarray) -> float:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 30 or np.std(x[m]) == 0 or np.std(y[m]) == 0:
        return 0.0
    return float(np.corrcoef(x[m], y[m])[0, 1])


def quality(bars: dict[str, pd.DataFrame], macro: pd.DataFrame) -> dict:
    q = {"bars": {}, "macro": {}}
    for sym, df in bars.items():
        idx = df.index
        gaps = int((idx.to_series().diff().dt.days.fillna(1) > 1).sum())
        q["bars"][sym] = {
            "rows": len(df), "start": str(idx.min().date()), "end": str(idx.max().date()),
            "missing_days_gaps": gaps, "dup_dates": int(idx.duplicated().sum()),
            "zero_volume_rows": int((df["volume"] <= 0).sum()),
            "nonfinite_close": int((~np.isfinite(df["close"])).sum()),
        }
    for c in MACRO_FEATURE_COLS:
        s = macro[c]
        nonzero = s[s != 0]
        q["macro"][c] = {
            "coverage_rows": int(s.notna().sum()), "nan": int(s.isna().sum()),
            "std": round(float(s.std()), 6), "min": round(float(s.min()), 4),
            "max": round(float(s.max()), 4),
            "degraded": bool(s.std() < 1e-6 or len(nonzero) < len(s) * 0.5),
        }
    return q


def signal(bars: dict[str, pd.DataFrame], macro: pd.DataFrame, weekly_h: int, daily_h: int) -> dict:
    feat_pool = {c: [] for c in MACRO_FEATURE_COLS}
    mom_pool, fwd_w_pool, fwd_d_pool, regime_pool = [], [], [], []
    for sym, df in bars.items():
        close = df["close"].astype(float)
        fwd_w = (close.shift(-weekly_h) / close - 1.0)
        fwd_d = (close.shift(-daily_h) / close - 1.0)
        mom = (close / close.shift(weekly_h) - 1.0)
        m = macro.reindex(df.index).ffill()
        for c in MACRO_FEATURE_COLS:
            feat_pool[c].append(m[c].to_numpy())
        mom_pool.append(mom.to_numpy())
        fwd_w_pool.append(fwd_w.to_numpy()); fwd_d_pool.append(fwd_d.to_numpy())
        regime_pool.append(m.apply(lambda r: regime_readout(r.to_dict())["regime"], axis=1).to_numpy())

    fwd_w = np.concatenate(fwd_w_pool); fwd_d = np.concatenate(fwd_d_pool)
    mom = np.concatenate(mom_pool); reg = np.concatenate(regime_pool)

    ic = {c: {"ic_weekly": round(_ic(np.concatenate(feat_pool[c]), fwd_w), 4),
              "ic_daily": round(_ic(np.concatenate(feat_pool[c]), fwd_d), 4)}
          for c in MACRO_FEATURE_COLS}
    ic["_momentum_baseline"] = {"ic_weekly": round(_ic(mom, fwd_w), 4),
                                "ic_daily": round(_ic(mom, fwd_d), 4)}

    regime_stats = {}
    for label in ("EXPANDING", "NEUTRAL", "CONTRACTING"):
        sel = (reg == label) & np.isfinite(fwd_w)
        n = int(sel.sum())
        regime_stats[label] = {
            "n": n,
            "mean_fwd_weekly": round(float(np.nanmean(fwd_w[sel])), 4) if n else None,
            "win_rate": round(float((fwd_w[sel] > 0).mean()), 3) if n else None,
        }

    # baseline directional accuracy: momentum sign vs forward sign (non-flat)
    base_dir = np.sign(mom); truth = np.sign(fwd_w)
    nz = np.isfinite(base_dir) & np.isfinite(truth) & (truth != 0)
    base_acc = round(float((base_dir[nz] == truth[nz]).mean()), 4) if nz.sum() else None

    return {"information_coefficient": ic, "regime_forward_returns": regime_stats,
            "momentum_baseline_dir_acc": base_acc, "n_samples": int(np.isfinite(fwd_w).sum())}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", default="BTC,ETH,SOL")
    p.add_argument("--bars-dir", default=str(ROOT / "data" / "bars"))
    p.add_argument("--macro", default=str(ROOT / "data" / "macro" / "features.csv"))
    p.add_argument("--weekly-h", type=int, default=10)
    p.add_argument("--daily-h", type=int, default=2)
    p.add_argument("--report-dir", default=str(ROOT / "data" / "reports"))
    args = p.parse_args()

    macro = pd.read_csv(args.macro, index_col="date", parse_dates=True)[MACRO_FEATURE_COLS]
    macro.index = macro.index.normalize()
    syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    bars = {s: _load_bars(Path(args.bars_dir) / f"{s}.csv") for s in syms}
    bars = {s: d for s, d in bars.items() if d is not None}
    if not bars:
        sys.exit("no bars found — run fetch_history --interval 1d first")

    report = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "quality": quality(bars, macro),
              "signal": signal(bars, macro, args.weekly_h, args.daily_h)}

    rep_dir = Path(args.report_dir); rep_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    (rep_dir / f"contextual_data_analysis_{stamp}.md").write_text(
        f"# Contextual data analysis ({stamp})\n\n```json\n{json.dumps(report, indent=2)}\n```\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
