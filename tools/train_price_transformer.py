#!/usr/bin/env python
"""Train a price transformer per symbol on bars in data/bars/<SYMBOL>.csv.

Saves checkpoints to data/models/<SYMBOL>.pt.
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
    p.add_argument("--bars-dir", default=str(ROOT / "data" / "bars"))
    p.add_argument("--out-dir", default=str(ROOT / "data" / "models"))
    p.add_argument("--symbols", default="",
                   help="comma-sep filter; default = all CSVs in bars-dir")
    p.add_argument("--seq-len", type=int, default=168)
    p.add_argument("--horizon", type=int, default=24)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=3e-4)
    args = p.parse_args()

    try:
        import torch  # noqa: F401
    except ImportError:
        sys.exit("torch not installed; pip install torch (CPU build is fine)")

    from deepCommodity.model.price_transformer import (  # noqa: E402
        TrainConfig,
        TransformerConfig,
        build_model,
        fit,
        make_features,
        make_labels,
        windowize,
    )

    bars_dir = Path(args.bars_dir)
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(bars_dir.glob("*.csv"))
    if args.symbols:
        wanted = {s.strip().upper() for s in args.symbols.split(",")}
        files = [f for f in files if f.stem.upper() in wanted]
    if not files:
        sys.exit(f"no CSVs in {bars_dir}")

    summary = {}
    for f in files:
        sym = f.stem.upper()
        df = pd.read_csv(f)
        feats = make_features(df)
        labels = make_labels(df, horizon=args.horizon)
        X, y = windowize(feats, labels, seq_len=args.seq_len, horizon=args.horizon)
        if len(X) < 200:
            print(f"  {sym}: skipped — only {len(X)} windows", file=sys.stderr)
            summary[sym] = {"status": "skipped", "n_windows": len(X)}
            continue

        cfg = TransformerConfig(seq_len=args.seq_len, horizon=args.horizon)
        model = build_model(cfg)
        hist = fit(model, X, y, TrainConfig(epochs=args.epochs,
                                            batch_size=args.batch_size, lr=args.lr))

        import torch
        ckpt_path = out_dir / f"{sym}.pt"
        torch.save({"state_dict": model.state_dict(),
                    "config": cfg.__dict__,
                    "history": hist}, ckpt_path)
        summary[sym] = {
            "status": "trained",
            "n_windows": len(X),
            "best_val_loss": round(hist["best_val_loss"], 4),
            "final_val_acc": round(hist["val_acc"][-1], 4) if hist["val_acc"] else None,
            "checkpoint": str(ckpt_path),
        }
        print(f"  {sym}: val_loss={hist['best_val_loss']:.4f} "
              f"acc={hist['val_acc'][-1]:.3f} -> {ckpt_path}", file=sys.stderr)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
