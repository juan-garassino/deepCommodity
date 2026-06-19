#!/usr/bin/env python
"""Train the macro-contextual transformer jointly across BTC/ETH/SOL.

Chronological train/val split (no shuffling across the time boundary), train-only
normalization, multi-head cross-entropy (weekly + daily), early stopping on the
weekly val loss (the horizon we validate/promote first). Saves a single global
checkpoint data/models/contextual.pt and a training report.
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
    HORIZONS, ContextualConfig, apply_norm, build_model, fit_norm,
)


def _split(dates: np.ndarray, val_frac: float) -> tuple[np.ndarray, np.ndarray]:
    """Chronological split: earliest (1-val_frac) train, latest val. Returns index masks."""
    order = np.argsort(dates, kind="stable")
    cut = int(len(order) * (1 - val_frac))
    tr = np.zeros(len(dates), bool); va = np.zeros(len(dates), bool)
    tr[order[:cut]] = True; va[order[cut:]] = True
    return tr, va


def train(ds_path: Path, out: Path, epochs: int, batch_size: int, lr: float,
          weight_decay: float, val_frac: float, patience: int) -> dict:
    import torch
    from torch import nn

    d = np.load(ds_path)
    meta = json.loads(ds_path.with_suffix(".meta.json").read_text())
    price_X, macro_X = d["price_X"], d["macro_X"]
    aid, dates = d["asset_id"], d["dates"]
    ys = {"weekly": d["y_weekly"], "daily": d["y_daily"]}

    tr, va = _split(dates, val_frac)
    norm = fit_norm(price_X[tr], macro_X[tr])          # fit on TRAIN only
    px, mx = apply_norm(price_X, macro_X, norm)

    cfg = ContextualConfig(
        price_seq=meta["price_seq"], price_feats=price_X.shape[-1],
        macro_seq=meta["macro_seq"], macro_feats=macro_X.shape[-1],
        n_assets=len(meta["symbols"]), weekly_h=meta["weekly_h"], daily_h=meta["daily_h"],
    )
    model = build_model(cfg)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = nn.CrossEntropyLoss()

    def batch(idx_pool, i):
        idx = idx_pool[i:i + batch_size]
        return (torch.from_numpy(px[idx]).float(), torch.from_numpy(mx[idx]).float(),
                torch.from_numpy(aid[idx]).long(),
                {h: torch.from_numpy(ys[h][idx]).long() for h in HORIZONS})

    tr_idx, va_idx = np.where(tr)[0], np.where(va)[0]
    hist = {"train_loss": [], "val_loss_weekly": [], "val_acc_weekly": [], "val_acc_daily": []}
    best, best_state, bad = float("inf"), None, 0

    for ep in range(epochs):
        model.train(); perm = np.random.permutation(tr_idx); tot = 0.0
        for i in range(0, len(perm), batch_size):
            pxb, mxb, ab, yb = batch(perm, i)
            logits = model(pxb, mxb, ab)
            loss = sum(loss_fn(logits[h], yb[h]) for h in HORIZONS)
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss) * len(yb["weekly"])
        model.eval()
        with torch.no_grad():
            pxb, mxb, ab, yb = batch(va_idx, 0) if False else (
                torch.from_numpy(px[va_idx]).float(), torch.from_numpy(mx[va_idx]).float(),
                torch.from_numpy(aid[va_idx]).long(),
                {h: torch.from_numpy(ys[h][va_idx]).long() for h in HORIZONS})
            vl = model(pxb, mxb, ab)
            vlw = float(loss_fn(vl["weekly"], yb["weekly"]))
            accw = float((vl["weekly"].argmax(-1) == yb["weekly"]).float().mean())
            accd = float((vl["daily"].argmax(-1) == yb["daily"]).float().mean())
        hist["train_loss"].append(tot / max(1, len(tr_idx)))
        hist["val_loss_weekly"].append(vlw)
        hist["val_acc_weekly"].append(accw); hist["val_acc_daily"].append(accd)
        if vlw < best - 1e-4:
            best, best_state, bad = vlw, {k: v.detach().cpu().clone()
                                          for k, v in model.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= patience:
                break

    if best_state:
        model.load_state_dict(best_state)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "config": cfg.__dict__, "norm": norm,
                "history": hist, "meta": meta,
                "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}, out)
    return {"best_val_loss_weekly": best,
            "val_acc_weekly": hist["val_acc_weekly"][-1] if hist["val_acc_weekly"] else None,
            "val_acc_daily": hist["val_acc_daily"][-1] if hist["val_acc_daily"] else None,
            "epochs_ran": len(hist["train_loss"]), "n_train": int(tr.sum()), "n_val": int(va.sum())}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default=str(ROOT / "data" / "contextual" / "dataset.npz"))
    p.add_argument("--out", default=str(ROOT / "data" / "models" / "contextual.pt"))
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--weight-decay", type=float, default=1e-3)
    p.add_argument("--val-frac", type=float, default=0.2)
    p.add_argument("--patience", type=int, default=6)
    p.add_argument("--report-dir", default=str(ROOT / "data" / "reports"))
    args = p.parse_args()

    summary = train(Path(args.dataset), Path(args.out), args.epochs, args.batch_size,
                    args.lr, args.weight_decay, args.val_frac, args.patience)
    rep_dir = Path(args.report_dir); rep_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    (rep_dir / f"contextual_train_{stamp}.md").write_text(
        f"# Contextual training report ({stamp})\n\n```json\n{json.dumps(summary, indent=2)}\n```\n")
    print(json.dumps({"out": args.out, **summary}, indent=2))


if __name__ == "__main__":
    main()
