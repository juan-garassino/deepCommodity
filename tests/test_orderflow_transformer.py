"""Phase 6 order-flow transformer: shape correctness + training step."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

torch = pytest.importorskip("torch")

from deepCommodity.model.orderflow_transformer import (  # noqa: E402
    OrderflowConfig,
    TrainConfig,
    build_model,
    fit,
    make_features,
    make_labels,
    predict_proba,
    proba_to_forecast,
    windowize,
)


def _synthetic_orderflow(n: int = 1500, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "ts": np.arange(n),
        "signed_volume": rng.normal(0, 5, n),
        "trade_count": rng.poisson(20, n),
        "mean_size": np.abs(rng.normal(0.5, 0.2, n)),
        "vwap_drift": rng.normal(0, 0.0005, n),
    })


def test_make_features_zscored():
    df = _synthetic_orderflow(1000)
    feats = make_features(df)
    assert feats.shape == (1000, 4)
    # rolling z-score should bring per-column mean ~ 0 over the tail
    tail_mu = feats[-300:].mean(axis=0)
    assert np.all(np.abs(tail_mu) < 0.5)


def test_make_labels_classes_present():
    df = _synthetic_orderflow(1000, seed=2)
    # Force some directional drift
    df.loc[100:200, "vwap_drift"] = 0.001
    df.loc[400:500, "vwap_drift"] = -0.001
    labels = make_labels(df, horizon_sec=30)
    assert set(np.unique(labels)).issubset({0, 1, 2})
    assert len(set(labels.tolist())) >= 2


def test_windowize_shapes():
    df = _synthetic_orderflow(1500)
    feats = make_features(df)
    labels = make_labels(df, horizon_sec=60)
    X, y = windowize(feats, labels, seq_len=600, horizon=60)
    assert X.shape[1:] == (600, 4)
    assert len(X) == len(y) == 1500 - 600 - 60


def test_orderflow_model_forward_shape():
    cfg = OrderflowConfig(seq_len=64, n_features=4, d_model=32, n_heads=4,
                          n_layers=2, dim_ff=64, n_classes=3)
    model = build_model(cfg)
    x = torch.randn(8, 64, 4)
    assert model(x).shape == (8, 3)


def test_orderflow_training_step_works():
    """Synthetic learnable task: label = sign of recent signed-volume sum.

    Deterministic — torch RNG seeded so the test is stable across suite ordering.
    """
    torch.manual_seed(0)
    n = 800
    rng = np.random.default_rng(7)
    feats = rng.normal(0, 1, (n, 4)).astype(np.float32)
    seq_len = 32
    labels = np.zeros(n, dtype=np.int64)
    for i in range(seq_len, n):
        s = feats[i - 16 : i, 0].sum()
        labels[i] = 0 if s < -0.5 else 2 if s > 0.5 else 1
    X, y = windowize(feats, labels[1:], seq_len=seq_len, horizon=1)

    cfg = OrderflowConfig(seq_len=seq_len, n_features=4, d_model=32, n_heads=4,
                          n_layers=2, dim_ff=64, dropout=0.0, n_classes=3)
    model = build_model(cfg)
    hist = fit(model, X, y, TrainConfig(epochs=12, batch_size=32, lr=1e-3, patience=20))
    # First few epochs may oscillate; require best loss to clear initial.
    assert min(hist["train_loss"]) < hist["train_loss"][0]


def test_proba_normalization():
    cfg = OrderflowConfig(seq_len=32, n_features=4, d_model=16, n_heads=2,
                          n_layers=1, dim_ff=32, n_classes=3)
    model = build_model(cfg)
    X = np.random.randn(5, 32, 4).astype(np.float32)
    proba = predict_proba(model, X)
    assert proba.shape == (5, 3)
    np.testing.assert_allclose(proba.sum(axis=1), 1.0, rtol=1e-5)


def test_proba_to_forecast_shared_helper():
    direction, conf = proba_to_forecast(np.array([0.05, 0.15, 0.80]))
    assert direction == "long" and conf > 0.6
