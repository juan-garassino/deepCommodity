"""Phase 6: order-flow transformer (specialist).

Trains on per-second order-flow features:
    [signed_volume, trade_count, mean_size, vwap_drift]
Window = last 600 seconds (10 min). Predicts direction over the next H seconds.

Same architecture family as `price_transformer.py` (transformer encoder + class
head); the encoder is reusable as a head for the Phase 8 fused model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    import torch  # noqa: F401

ORDERFLOW_FEATURES = ["signed_volume", "trade_count", "mean_size", "vwap_drift"]


def make_features(df: pd.DataFrame) -> np.ndarray:
    """Robust z-scoring on rolling window so model isn't sensitive to absolute scale."""
    out = np.stack([df[c].astype(float).to_numpy() for c in ORDERFLOW_FEATURES], axis=1)
    # rolling 5-min standardization
    win = 300
    if len(out) < win:
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
    mu = pd.DataFrame(out).rolling(win, min_periods=1).mean().to_numpy()
    sd = pd.DataFrame(out).rolling(win, min_periods=1).std().to_numpy()
    sd = np.where(sd < 1e-9, 1.0, sd)
    z = (out - mu) / sd
    return np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0)


def make_labels(df: pd.DataFrame, horizon_sec: int = 60,
                up_thresh: float = 0.0008, down_thresh: float = -0.0008) -> np.ndarray:
    """Direction label = sign of cumulative vwap_drift over the next horizon_sec."""
    drift = df["vwap_drift"].astype(float).to_numpy()
    fwd = np.zeros(len(drift), dtype=float)
    for i in range(len(drift) - horizon_sec):
        fwd[i] = drift[i + 1 : i + 1 + horizon_sec].sum()
    labels = np.full(len(drift), 1, dtype=np.int64)
    labels[fwd >= up_thresh] = 2
    labels[fwd <= down_thresh] = 0
    return labels


def windowize(features: np.ndarray, labels: np.ndarray,
              seq_len: int = 600, horizon: int = 60) -> tuple[np.ndarray, np.ndarray]:
    n = len(features) - seq_len - horizon
    if n <= 0:
        return np.empty((0, seq_len, features.shape[1])), np.empty((0,), dtype=np.int64)
    X = np.lib.stride_tricks.sliding_window_view(features, (seq_len, features.shape[1]))[
        :n, 0, :, :
    ]
    y = labels[seq_len - 1 : seq_len - 1 + n]
    return np.ascontiguousarray(X), np.ascontiguousarray(y)


@dataclass
class OrderflowConfig:
    seq_len: int = 600
    n_features: int = 4
    d_model: int = 64
    n_heads: int = 4
    n_layers: int = 4
    dim_ff: int = 128
    dropout: float = 0.1
    n_classes: int = 3
    horizon: int = 60


def _torch():
    import torch
    from torch import nn
    return torch, nn


def build_model(cfg: OrderflowConfig | None = None):
    torch, nn = _torch()
    cfg = cfg or OrderflowConfig()

    class OrderflowTransformer(nn.Module):
        def __init__(self, c: OrderflowConfig):
            super().__init__()
            self.c = c
            self.input_proj = nn.Linear(c.n_features, c.d_model)
            self.pos = nn.Parameter(torch.zeros(1, c.seq_len, c.d_model))
            enc_layer = nn.TransformerEncoderLayer(
                d_model=c.d_model, nhead=c.n_heads, dim_feedforward=c.dim_ff,
                dropout=c.dropout, batch_first=True, activation="gelu",
            )
            self.encoder = nn.TransformerEncoder(enc_layer, num_layers=c.n_layers)
            self.head = nn.Sequential(nn.LayerNorm(c.d_model),
                                      nn.Linear(c.d_model, c.n_classes))

        def encode(self, x):
            h = self.input_proj(x) + self.pos[:, : x.size(1)]
            return self.encoder(h)

        def forward(self, x):
            h = self.encode(x)
            return self.head(h[:, -1])

    return OrderflowTransformer(cfg)


# Reuse the same training helpers from price_transformer to avoid drift
from deepCommodity.model.price_transformer import (  # noqa: E402
    TrainConfig,
    fit,
    predict_proba,
    proba_to_forecast,
)

__all__ = [
    "ORDERFLOW_FEATURES", "OrderflowConfig", "TrainConfig",
    "make_features", "make_labels", "windowize",
    "build_model", "fit", "predict_proba", "proba_to_forecast",
]
