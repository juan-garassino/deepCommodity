"""Phase 5: price transformer (specialist).

Trains on OHLCV bars across the universe. Per-symbol for v1; cross-asset
attention is a v2 follow-up. Output is a 3-class direction softmax (down /
flat / up) over the next H bars, so it slots cleanly into the agent's
forecast.confidence ∈ [0, 1] interface.

PyTorch is lazy-imported. Importing this module without torch installed
raises only when you call build_model / fit / predict.

Inputs (per symbol):
    raw bars : DataFrame with columns [open, high, low, close, volume]
    -> features: [pct_close, log_vol_chg, hl_spread, oc_spread]   shape (T, 4)
    -> windows : sliding (seq_len=168, 4) -> label = sign of pct_change at t+h

Outputs:
    logits over {down, flat, up} per window.
    Inference returns (direction, confidence) compatible with backtest.engine.Forecast.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:  # only for type hints, no runtime torch import
    import torch
    from torch import nn

FEATURE_COLS = ["pct_close", "log_vol_chg", "hl_spread", "oc_spread"]


# ---- featurization ---------------------------------------------------------

def make_features(df: pd.DataFrame) -> np.ndarray:
    """Convert OHLCV DataFrame -> (T, 4) feature matrix. Drops first row (NaN)."""
    eps = 1e-12
    pct_close = df["close"].pct_change()
    log_vol_chg = np.log(df["volume"] + eps).diff()
    hl_spread = (df["high"] - df["low"]) / (df["close"] + eps)
    oc_spread = (df["close"] - df["open"]) / (df["open"] + eps)
    feats = np.stack([pct_close, log_vol_chg, hl_spread, oc_spread], axis=1)
    feats = np.nan_to_num(feats, nan=0.0, posinf=0.0, neginf=0.0)
    return feats[1:]  # drop first row


def make_labels(df: pd.DataFrame, horizon: int = 24,
                up_thresh: float = 0.005, down_thresh: float = -0.005) -> np.ndarray:
    """Return integer labels {0=down, 1=flat, 2=up} per row, shifted by horizon."""
    fwd = df["close"].shift(-horizon) / df["close"] - 1.0
    labels = np.full(len(df), 1, dtype=np.int64)  # default flat
    labels[fwd >= up_thresh] = 2
    labels[fwd <= down_thresh] = 0
    return labels[1:]  # align with make_features which drops row 0


def windowize(features: np.ndarray, labels: np.ndarray,
              seq_len: int = 168, horizon: int = 24) -> tuple[np.ndarray, np.ndarray]:
    """Build (N, seq_len, F) X and (N,) y. Drops the last `horizon` rows (no future label)."""
    n = len(features) - seq_len - horizon
    if n <= 0:
        return np.empty((0, seq_len, features.shape[1])), np.empty((0,), dtype=np.int64)
    X = np.lib.stride_tricks.sliding_window_view(features, (seq_len, features.shape[1]))[
        :n, 0, :, :
    ]
    y = labels[seq_len - 1 : seq_len - 1 + n]
    return np.ascontiguousarray(X), np.ascontiguousarray(y)


# ---- model -----------------------------------------------------------------

@dataclass
class TransformerConfig:
    seq_len: int = 168
    n_features: int = 4
    d_model: int = 64
    n_heads: int = 4
    n_layers: int = 4
    dim_ff: int = 128
    dropout: float = 0.1
    n_classes: int = 3
    horizon: int = 24


def _torch_modules():
    """Import torch lazily and return the symbols we need."""
    import torch
    from torch import nn
    return torch, nn


def build_model(cfg: TransformerConfig | None = None):
    """Build a torch.nn.Module. Raises ImportError if torch is missing."""
    torch, nn = _torch_modules()
    cfg = cfg or TransformerConfig()

    class PriceTransformer(nn.Module):
        def __init__(self, c: TransformerConfig):
            super().__init__()
            self.c = c
            self.input_proj = nn.Linear(c.n_features, c.d_model)
            # learned positional embedding (small seq_len, fine to be learned)
            self.pos = nn.Parameter(torch.zeros(1, c.seq_len, c.d_model))
            enc_layer = nn.TransformerEncoderLayer(
                d_model=c.d_model, nhead=c.n_heads, dim_feedforward=c.dim_ff,
                dropout=c.dropout, batch_first=True, activation="gelu",
            )
            self.encoder = nn.TransformerEncoder(enc_layer, num_layers=c.n_layers)
            self.head = nn.Sequential(
                nn.LayerNorm(c.d_model),
                nn.Linear(c.d_model, c.n_classes),
            )

        def encode(self, x):
            # x: (B, T, F) -> (B, T, d_model)
            h = self.input_proj(x) + self.pos[:, : x.size(1)]
            return self.encoder(h)

        def forward(self, x):
            h = self.encode(x)
            # use last-step representation as the prediction summary
            return self.head(h[:, -1])

    return PriceTransformer(cfg)


# ---- training --------------------------------------------------------------

def _auto_device() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


@dataclass
class TrainConfig:
    epochs: int = 20
    batch_size: int = 64
    lr: float = 3e-4
    weight_decay: float = 1e-4
    val_frac: float = 0.2
    patience: int = 4
    device: str = field(default_factory=_auto_device)
    num_workers: int = 0
    pin_memory: bool = False


def fit(model, X: np.ndarray, y: np.ndarray, cfg: TrainConfig | None = None) -> dict:
    """Train with early stopping on val cross-entropy. Returns history dict."""
    torch, nn = _torch_modules()
    cfg = cfg or TrainConfig()
    device = torch.device(cfg.device)
    model = model.to(device)

    n = len(X)
    cut = int(n * (1 - cfg.val_frac))
    X_tr = torch.from_numpy(X[:cut]).float()
    y_tr = torch.from_numpy(y[:cut]).long()
    X_va = torch.from_numpy(X[cut:]).float()
    y_va = torch.from_numpy(y[cut:]).long()

    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    loss_fn = nn.CrossEntropyLoss()

    history = {"train_loss": [], "val_loss": [], "val_acc": []}
    best_val = float("inf")
    best_state = None
    bad = 0

    for ep in range(cfg.epochs):
        model.train()
        perm = torch.randperm(len(X_tr))
        train_loss_sum = 0.0
        for i in range(0, len(X_tr), cfg.batch_size):
            idx = perm[i : i + cfg.batch_size]
            xb, yb = X_tr[idx].to(device), y_tr[idx].to(device)
            logits = model(xb)
            loss = loss_fn(logits, yb)
            opt.zero_grad(); loss.backward(); opt.step()
            train_loss_sum += loss.item() * len(idx)
        train_loss = train_loss_sum / max(1, len(X_tr))

        model.eval()
        with torch.no_grad():
            xb, yb = X_va.to(device), y_va.to(device)
            logits = model(xb)
            val_loss = loss_fn(logits, yb).item()
            val_acc = (logits.argmax(-1) == yb).float().mean().item()

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        if val_loss < best_val - 1e-4:
            best_val = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            bad = 0
        else:
            bad += 1
            if bad >= cfg.patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    history["best_val_loss"] = best_val
    return history


def predict_proba(model, X: np.ndarray, batch_size: int = 256) -> np.ndarray:
    torch, nn = _torch_modules()
    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(X), batch_size):
            xb = torch.from_numpy(X[i : i + batch_size]).float()
            logits = model(xb)
            out.append(torch.softmax(logits, dim=-1).cpu().numpy())
    return np.concatenate(out, axis=0) if out else np.empty((0, 3))


def proba_to_forecast(proba: np.ndarray, min_conf: float = 0.0) -> tuple[str, float]:
    """Map a single (3,) proba vector -> (direction, confidence).

    Confidence is the margin between the top class and uniform (1/3), scaled to [0,1].
    """
    classes = ["short", "flat", "long"]
    top = int(np.argmax(proba))
    conf = float((proba[top] - 1 / 3) / (2 / 3))
    conf = max(0.0, min(1.0, conf))
    if conf < min_conf:
        return "flat", conf
    return classes[top], conf
