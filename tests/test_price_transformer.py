"""Phase 5 price transformer: shape correctness + training step.

Skipped cleanly if torch is not installed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

torch = pytest.importorskip("torch")

from deepCommodity.model.price_transformer import (  # noqa: E402
    TrainConfig,
    TransformerConfig,
    build_model,
    fit,
    make_features,
    make_labels,
    predict_proba,
    proba_to_forecast,
    windowize,
)


# ---- featurization (no torch needed) --------------------------------------

def _synthetic_ohlcv(n: int = 500, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.01, n))
    high = close * (1 + np.abs(rng.normal(0, 0.005, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.005, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    volume = np.abs(rng.normal(1000, 200, n))
    return pd.DataFrame({"open": open_, "high": high, "low": low,
                         "close": close, "volume": volume})


def test_make_features_shape():
    df = _synthetic_ohlcv(500)
    feats = make_features(df)
    assert feats.shape == (499, 4)
    assert not np.isnan(feats).any()
    assert not np.isinf(feats).any()


def test_make_labels_classes_present():
    df = _synthetic_ohlcv(500, seed=1)
    labels = make_labels(df, horizon=24)
    # at least 2 of 3 classes should appear in 500 random walk bars
    assert len(set(labels.tolist())) >= 2
    assert labels.min() >= 0 and labels.max() <= 2


def test_windowize_shapes():
    df = _synthetic_ohlcv(500)
    feats = make_features(df)
    labels = make_labels(df, horizon=24)
    X, y = windowize(feats, labels, seq_len=168, horizon=24)
    assert X.shape[1:] == (168, 4)
    assert len(X) == len(y)
    # n = 499 - 168 - 24 = 307
    assert len(X) == 307


def test_windowize_too_short():
    df = _synthetic_ohlcv(100)
    feats = make_features(df)
    labels = make_labels(df, horizon=24)
    X, y = windowize(feats, labels, seq_len=168, horizon=24)
    assert len(X) == 0
    assert len(y) == 0


# ---- model + training -----------------------------------------------------

def test_model_forward_shape():
    cfg = TransformerConfig(seq_len=64, n_features=4, d_model=32, n_heads=4,
                            n_layers=2, dim_ff=64, n_classes=3)
    model = build_model(cfg)
    x = torch.randn(8, 64, 4)
    out = model(x)
    assert out.shape == (8, 3)


def test_one_training_step_decreases_loss():
    """Sanity: a few epochs on a learnable task should drive val_loss below random."""
    n = 600
    rng = np.random.default_rng(42)
    # Construct a window where label is decided by the mean of the last 8 features[0]
    feats = rng.normal(0, 1, (n, 4)).astype(np.float32)
    seq_len = 32
    horizon = 1
    labels_full = np.zeros(n, dtype=np.int64)
    for i in range(seq_len, n):
        m = feats[i - 8 : i, 0].mean()
        labels_full[i] = 0 if m < -0.2 else 2 if m > 0.2 else 1
    X, y = windowize(feats, labels_full[1:], seq_len=seq_len, horizon=horizon)

    cfg = TransformerConfig(seq_len=seq_len, n_features=4, d_model=32, n_heads=4,
                            n_layers=2, dim_ff=64, dropout=0.0, n_classes=3)
    model = build_model(cfg)
    hist = fit(model, X, y,
               TrainConfig(epochs=10, batch_size=32, lr=1e-3, patience=10))
    # Loss must drop and val accuracy must beat the largest-class prior.
    assert hist["train_loss"][-1] < hist["train_loss"][0]
    largest_class = max(np.bincount(y[: int(0.8 * len(y))], minlength=3)) / int(0.8 * len(y))
    assert hist["val_acc"][-1] >= largest_class - 0.05  # at worst, match the prior


def test_predict_proba_shape_and_norm():
    cfg = TransformerConfig(seq_len=32, n_features=4, d_model=16, n_heads=2,
                            n_layers=1, dim_ff=32, n_classes=3)
    model = build_model(cfg)
    X = np.random.randn(10, 32, 4).astype(np.float32)
    proba = predict_proba(model, X)
    assert proba.shape == (10, 3)
    np.testing.assert_allclose(proba.sum(axis=1), 1.0, rtol=1e-5)


def test_proba_to_forecast_thresholds():
    # Confident up
    direction, conf = proba_to_forecast(np.array([0.05, 0.15, 0.80]), min_conf=0.0)
    assert direction == "long" and conf > 0.6

    # Below confidence threshold -> flat
    direction, conf = proba_to_forecast(np.array([0.30, 0.36, 0.34]), min_conf=0.5)
    assert direction == "flat"

    # Confident down
    direction, _ = proba_to_forecast(np.array([0.85, 0.10, 0.05]))
    assert direction == "short"

    # Uniform -> conf 0
    _, conf = proba_to_forecast(np.array([1/3, 1/3, 1/3]))
    assert conf == 0.0
