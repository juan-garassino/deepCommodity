#!/usr/bin/env python
"""Train an order-flow transformer per symbol on per-second flow features.

Mirrors tools/train_price_transformer.py for the orderflow modality.
Saves checkpoints to <out-dir>/<SYMBOL>.orderflow.pt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--orderflow-dir", default=str(ROOT / "data" / "orderflow"))
    p.add_argument("--out-dir", default=str(ROOT / "data" / "models"))
    p.add_argument("--symbols", default="",
                   help="comma-sep filter; default = all CSVs in orderflow-dir")
    p.add_argument("--seq-len", type=int, default=600)
    p.add_argument("--horizon-sec", type=int, default=60)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=128)
    p.add_argument("--lr", type=float, default=3e-4)
    args = p.parse_args()

    try:
        import torch
    except ImportError:
        sys.exit("torch not installed; pip install torch")

    from deepCommodity.model.orderflow_transformer import (  # noqa: E402
        OrderflowConfig,
        TrainConfig,
        build_model,
        fit,
        make_features,
        make_labels,
        windowize,
    )

    src = Path(args.orderflow_dir)
    dst = Path(args.out_dir); dst.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob("*.csv"))
    if args.symbols:
        wanted = {s.strip().upper() for s in args.symbols.split(",")}
        files = [f for f in files if f.stem.upper() in wanted]
    if not files:
        sys.exit(f"no CSVs in {src}")

    summary = {}
    for f in files:
        sym = f.stem.upper()
        df = pd.read_csv(f)
        feats = make_features(df)
        labels = make_labels(df, horizon_sec=args.horizon_sec)
        X, y = windowize(feats, labels, seq_len=args.seq_len, horizon=args.horizon_sec)
        if len(X) < 200:
            print(f"  {sym}: skipped — only {len(X)} windows", file=sys.stderr)
            summary[sym] = {"status": "skipped", "n_windows": len(X)}
            continue

        cfg = OrderflowConfig(seq_len=args.seq_len, horizon=args.horizon_sec)
        model = build_model(cfg)
        hist = fit(model, X, y, TrainConfig(epochs=args.epochs,
                                            batch_size=args.batch_size, lr=args.lr))

        ckpt = dst / f"{sym}.orderflow.pt"
        torch.save({"state_dict": model.state_dict(),
                    "config": cfg.__dict__,
                    "history": hist}, ckpt)
        summary[sym] = {
            "status": "trained", "n_windows": len(X),
            "best_val_loss": round(hist["best_val_loss"], 4),
            "final_val_acc": round(hist["val_acc"][-1], 4) if hist["val_acc"] else None,
            "checkpoint": str(ckpt),
        }
        print(f"  {sym}: val_loss={hist['best_val_loss']:.4f} -> {ckpt}", file=sys.stderr)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
