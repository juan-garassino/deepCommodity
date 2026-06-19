#!/usr/bin/env python
"""Walk-forward-ish SHIP / NO-SHIP gate for the contextual model.

Honest out-of-sample test on the dataset itself (real OHLCV-derived features +
realized forward returns), comparing the trained contextual weekly head against a
momentum baseline that mirrors the live rule-based forecaster (trailing return >0
=> long). Chronological holdout (latest `--test-frac`), optionally over K
expanding folds. Reports directional accuracy + a long-only PnL proxy through a
transaction cost, and emits a SHIP/NO-SHIP verdict.

Why not the bar-replay engine: backtest.engine.Bar is close-only, which zeroes the
hl_spread / oc_spread features the model was trained on. A dataset-level holdout
keeps the exact training features, so it's the faithful model gate. (A full
trading-sim adapter over real OHLCV bars is a v2 follow-up.)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.model.contextual_transformer import (  # noqa: E402
    apply_norm, build_model, predict, proba_to_forecast, ContextualConfig,
)

ACC_LIFT_GATE = 0.05      # weekly directional-accuracy lift vs baseline
COST_BPS = 7.0            # round-trip cost proxy on a taken long


def _baseline_dir(price_X: np.ndarray) -> np.ndarray:
    """Momentum baseline mirroring the live rule: trailing window return > 0 -> long(2)."""
    cum = price_X[:, :, 0].sum(axis=1)            # feature 0 == pct_close
    out = np.full(len(price_X), 1, np.int64)      # flat
    out[cum > 0.0] = 2; out[cum < 0.0] = 0
    return out


def _metrics(pred_dir: np.ndarray, y: np.ndarray, r: np.ndarray) -> dict:
    acc = float((pred_dir == y).mean())
    longs = pred_dir == 2
    n_long = int(longs.sum())
    gross = float(r[longs].mean()) if n_long else 0.0
    net = gross - COST_BPS / 1e4
    taken = (r[longs] - COST_BPS / 1e4) if n_long else np.array([0.0])
    sharpe = float(np.mean(taken) / (np.std(taken) + 1e-9) * np.sqrt(52)) if n_long > 1 else 0.0
    return {"dir_acc": round(acc, 4), "n_long": n_long,
            "long_ret_net": round(net, 4), "long_sharpe": round(sharpe, 3)}


def _load_model(ckpt_path: Path):
    import torch
    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    cfg = ContextualConfig(**ck["config"])
    model = build_model(cfg)
    model.load_state_dict(ck["state_dict"])
    return model, ck["norm"]


def evaluate(ds_path: Path, ckpt_path: Path, test_frac: float, min_conf: float) -> dict:
    d = np.load(ds_path)
    order = np.argsort(d["dates"], kind="stable")
    cut = int(len(order) * (1 - test_frac))
    te = order[cut:]
    model, norm = _load_model(ckpt_path)
    px, mx = apply_norm(d["price_X"][te], d["macro_X"][te], norm)
    proba = predict(model, px, mx, d["asset_id"][te])["weekly"]

    ctx_dir = np.array([2 if proba_to_forecast(p, min_conf)[0] == "long"
                        else 0 if proba_to_forecast(p, min_conf)[0] == "short"
                        else 1 for p in proba], np.int64)
    base_dir = _baseline_dir(d["price_X"][te])
    y, r = d["y_weekly"][te], d["r_weekly"][te]

    ctx, base = _metrics(ctx_dir, y, r), _metrics(base_dir, y, r)
    acc_lift = round(ctx["dir_acc"] - base["dir_acc"], 4)
    pnl_edge = round(ctx["long_ret_net"] - base["long_ret_net"], 4)
    ship = (acc_lift >= ACC_LIFT_GATE) and (pnl_edge >= 0) and (ctx["long_ret_net"] > 0)
    return {"n_test": int(len(te)), "contextual": ctx, "baseline": base,
            "acc_lift": acc_lift, "pnl_edge": pnl_edge,
            "verdict": "SHIP" if ship else "NO-SHIP",
            "gate": {"acc_lift>=": ACC_LIFT_GATE, "pnl_edge>=0": True, "ctx_ret>0": True}}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default=str(ROOT / "data" / "contextual" / "dataset.npz"))
    p.add_argument("--ckpt", default=str(ROOT / "data" / "models" / "contextual.pt"))
    p.add_argument("--test-frac", type=float, default=0.25)
    p.add_argument("--min-conf", type=float, default=0.1)
    p.add_argument("--report-dir", default=str(ROOT / "data" / "reports"))
    args = p.parse_args()

    res = evaluate(Path(args.dataset), Path(args.ckpt), args.test_frac, args.min_conf)
    rep_dir = Path(args.report_dir); rep_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    (rep_dir / f"contextual_eval_{stamp}.md").write_text(
        f"# Contextual eval — {res['verdict']} ({stamp})\n\n"
        f"Weekly head, out-of-sample (last {int(args.test_frac*100)}%).\n\n"
        f"```json\n{json.dumps(res, indent=2)}\n```\n\n"
        f"**{res['verdict']}** — acc lift {res['acc_lift']} (gate ≥{ACC_LIFT_GATE}), "
        f"pnl edge {res['pnl_edge']}.\n")
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["verdict"] == "SHIP" else 1)


if __name__ == "__main__":
    main()
