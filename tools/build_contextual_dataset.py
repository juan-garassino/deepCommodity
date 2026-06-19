#!/usr/bin/env python
"""Build the contextual training dataset: daily price windows + the point-in-time
macro window, jointly across assets, with multi-horizon labels.

For each asset and each prediction date D (the close of a daily bar):
  price_X : last `price_seq` daily price-feature rows up to D        (price_seq, 4)
  macro_X : the macro-panel rows for the `macro_seq` days up to D     (macro_seq, K)
  y_weekly: sign of the forward return over `weekly_h` days past D    {0,1,2}
  y_daily : sign of the forward return over `daily_h` days past D     {0,1,2}
  date    : D (ordinal) — used for chronological / walk-forward splits
  asset_id: index into the asset list

Macro rows are sliced as-of D (`macro.loc[:D]`); features.csv is already
publication-lag-shifted, so this slice is leakage-free by construction. Reuses
make_features / make_labels from the price transformer for the price channel.

Output: data/contextual/dataset.npz (+ meta.json sidecar).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.model.price_transformer import make_features, make_labels  # noqa: E402
from tools.fetch_macro_features import MACRO_FEATURE_COLS  # noqa: E402


def _build_one(sym: str, asset_id: int, bars_csv: Path, macro: pd.DataFrame,
               price_seq: int, macro_seq: int, weekly_h: int, daily_h: int,
               up: float, down: float) -> dict | None:
    if not bars_csv.exists():
        return None
    df = pd.read_csv(bars_csv)
    if "ts" not in df.columns or len(df) < price_seq + weekly_h + 5:
        return None
    ts = pd.to_datetime(df["ts"], unit="ms" if np.issubdtype(df["ts"].dtype, np.number) else None)
    ts = ts.dt.normalize()

    feats = make_features(df)                       # (T-1, 4); feats[k] -> bar k+1
    y_wk = make_labels(df, weekly_h, up, down)      # aligned to feats (drops row 0)
    y_dl = make_labels(df, daily_h, up, down)
    # realized forward returns, aligned to feats (so the eval can compute real PnL)
    r_wk = (df["close"].shift(-weekly_h) / df["close"] - 1.0).to_numpy()[1:]
    r_dl = (df["close"].shift(-daily_h) / df["close"] - 1.0).to_numpy()[1:]
    bar_dates = ts.values[1:]                       # date for feats[k]

    px, mx, yw, yd, rw, rd, dates = [], [], [], [], [], [], []
    for j in range(price_seq - 1, len(feats) - weekly_h):
        D = pd.Timestamp(bar_dates[j]).normalize()
        mwin = macro.loc[:D]
        if len(mwin) < macro_seq:
            continue
        px.append(feats[j - price_seq + 1: j + 1])
        mx.append(mwin.tail(macro_seq).to_numpy())
        yw.append(int(y_wk[j])); yd.append(int(y_dl[j]))
        rw.append(float(np.nan_to_num(r_wk[j]))); rd.append(float(np.nan_to_num(r_dl[j])))
        dates.append(int(D.toordinal()))
    if not px:
        return None
    return {
        "price_X": np.asarray(px, dtype=np.float32),
        "macro_X": np.asarray(mx, dtype=np.float32),
        "y_weekly": np.asarray(yw, dtype=np.int64),
        "y_daily": np.asarray(yd, dtype=np.int64),
        "r_weekly": np.asarray(rw, dtype=np.float32),
        "r_daily": np.asarray(rd, dtype=np.float32),
        "dates": np.asarray(dates, dtype=np.int64),
        "asset_id": np.full(len(px), asset_id, dtype=np.int64),
        "symbol": sym,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", default="BTC,ETH,SOL")
    p.add_argument("--bars-dir", default=str(ROOT / "data" / "bars"))
    p.add_argument("--macro", default=str(ROOT / "data" / "macro" / "features.csv"))
    p.add_argument("--out", default=str(ROOT / "data" / "contextual" / "dataset.npz"))
    p.add_argument("--price-seq", type=int, default=90)
    p.add_argument("--macro-seq", type=int, default=60)
    p.add_argument("--weekly-h", type=int, default=10)
    p.add_argument("--daily-h", type=int, default=2)
    p.add_argument("--up", type=float, default=0.02)
    p.add_argument("--down", type=float, default=-0.02)
    args = p.parse_args()

    macro = pd.read_csv(args.macro, index_col="date", parse_dates=True)[MACRO_FEATURE_COLS]
    macro.index = macro.index.normalize()
    syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    bars_dir = Path(args.bars_dir)

    parts = []
    for aid, sym in enumerate(syms):
        part = _build_one(sym, aid, bars_dir / f"{sym}.csv", macro,
                          args.price_seq, args.macro_seq, args.weekly_h, args.daily_h,
                          args.up, args.down)
        if part:
            parts.append(part)
            print(f"  {sym}: {len(part['price_X'])} samples", file=sys.stderr)
        else:
            print(f"  {sym}: SKIPPED (missing bars or too short)", file=sys.stderr)
    if not parts:
        sys.exit("no samples built — fetch daily bars + macro features first")

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    merged = {k: np.concatenate([p[k] for p in parts]) for k in
              ("price_X", "macro_X", "y_weekly", "y_daily", "r_weekly", "r_daily",
               "dates", "asset_id")}
    np.savez_compressed(out, **merged)
    meta = {
        "symbols": syms, "n_samples": int(len(merged["price_X"])),
        "price_seq": args.price_seq, "macro_seq": args.macro_seq,
        "macro_feature_cols": MACRO_FEATURE_COLS,
        "weekly_h": args.weekly_h, "daily_h": args.daily_h,
        "label_thresholds": {"up": args.up, "down": args.down},
    }
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps({"out": str(out), **meta}, indent=2))


if __name__ == "__main__":
    main()
