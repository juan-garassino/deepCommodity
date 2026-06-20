"""Contextual transformer — model forward, normalization, and a train->eval smoke.

Motivating sources:
  deepCommodity/model/contextual_transformer.py
  tools/train_contextual.py  (train)
  tools/eval_contextual.py   (evaluate)
torch is a dev dependency; skip cleanly if absent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

torch = pytest.importorskip("torch")

from deepCommodity.model.contextual_transformer import (  # noqa: E402
    ContextualConfig, apply_norm, build_model, fit_norm, predict, proba_to_forecast)

TINY = ContextualConfig(price_seq=8, price_feats=4, macro_seq=6, macro_feats=7,
                        n_assets=2, d_model=16, n_heads=2, n_layers=1, dim_ff=32)


def test_forward_shapes_and_missing_macro():
    model = build_model(TINY)
    px = torch.randn(5, TINY.price_seq, TINY.price_feats)
    mx = torch.randn(5, TINY.macro_seq, TINY.macro_feats)
    aid = torch.tensor([0, 1, 0, 1, 0])
    out = model(px, mx, aid)
    assert set(out) == {"weekly", "daily"}
    assert out["weekly"].shape == (5, 3)
    # macro-missing path falls back to zeros, still produces logits
    out2 = model(px, None, aid)
    assert out2["daily"].shape == (5, 3)


def test_norm_roundtrip_and_predict():
    px = np.random.randn(20, TINY.price_seq, TINY.price_feats).astype(np.float32)
    mx = np.random.randn(20, TINY.macro_seq, TINY.macro_feats).astype(np.float32)
    norm = fit_norm(px, mx)
    pxn, mxn = apply_norm(px, mx, norm)
    assert abs(pxn.reshape(-1, 4).mean()) < 0.5     # roughly centered
    proba = predict(build_model(TINY), pxn, mxn, np.zeros(20, np.int64))
    assert proba["weekly"].shape == (20, 3)
    assert np.allclose(proba["weekly"].sum(1), 1.0, atol=1e-4)


def test_proba_to_forecast_mapping():
    assert proba_to_forecast(np.array([0.8, 0.1, 0.1]))[0] == "short"
    assert proba_to_forecast(np.array([0.1, 0.1, 0.8]))[0] == "long"
    # low margin + min_conf -> flat
    assert proba_to_forecast(np.array([0.34, 0.33, 0.33]), min_conf=0.5)[0] == "flat"


def _tiny_dataset(path: Path, n: int = 120):
    rng = np.random.default_rng(0)
    d = {
        "price_X": rng.standard_normal((n, TINY.price_seq, 4)).astype(np.float32),
        "macro_X": rng.standard_normal((n, TINY.macro_seq, 7)).astype(np.float32),
        "y_weekly": rng.integers(0, 3, n).astype(np.int64),
        "y_daily": rng.integers(0, 3, n).astype(np.int64),
        "r_weekly": (rng.standard_normal(n) * 0.05).astype(np.float32),
        "r_daily": (rng.standard_normal(n) * 0.02).astype(np.float32),
        "dates": np.arange(n, dtype=np.int64) + 730000,
        "asset_id": rng.integers(0, 2, n).astype(np.int64),
    }
    np.savez_compressed(path, **d)
    path.with_suffix(".meta.json").write_text(json.dumps({
        "symbols": ["BTC", "ETH"], "price_seq": TINY.price_seq, "macro_seq": TINY.macro_seq,
        "macro_feature_cols": list(range(7)), "weekly_h": 10, "daily_h": 2,
    }))


def test_train_then_eval_smoke(tmp_path):
    from tools.train_contextual import train
    from tools.eval_contextual import evaluate

    ds = tmp_path / "dataset.npz"
    _tiny_dataset(ds)
    ckpt = tmp_path / "contextual.pt"
    summary = train(ds, ckpt, epochs=2, batch_size=16, lr=1e-3,
                    weight_decay=1e-3, val_frac=0.2, patience=3)
    assert ckpt.exists() and summary["epochs_ran"] >= 1
    res = evaluate(ds, ckpt, test_frac=0.25, min_conf=0.1)
    assert res["verdict"] in {"SHIP", "NO-SHIP"}
    assert "dir_acc" in res["contextual"]
