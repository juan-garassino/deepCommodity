"""Macro-contextual transformer (v1, crypto-first).

A single model over BTC/ETH/SOL where a SHARED global-macro encoder (M2, net
liquidity, DXY, total-crypto-cap) conditions a per-asset price encoder. A learned
asset embedding distinguishes assets; a shared trunk feeds two horizon heads
(weekly, daily), each a 3-class direction softmax (down/flat/up) compatible with
the agent's forecast.confidence interface.

Reuses the encoder pattern from price_transformer.py. PyTorch is lazy-imported,
so importing this module without torch only fails when you build/fit/predict.
The regime readout is a transparent rule over the macro panel — NOT a learned
head — so the alert is trustworthy and needs no subjective regime labels.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import torch  # noqa: F401

HORIZONS = ("weekly", "daily")
CLASSES = ["short", "flat", "long"]   # index 0,1,2 == down,flat,up


@dataclass
class ContextualConfig:
    price_seq: int = 90
    price_feats: int = 4
    macro_seq: int = 60
    macro_feats: int = 7
    n_assets: int = 3
    d_model: int = 64
    n_heads: int = 4
    n_layers: int = 2          # small: daily crypto history is short
    dim_ff: int = 128
    dropout: float = 0.25      # heavy reg vs overfit
    n_classes: int = 3
    weekly_h: int = 10
    daily_h: int = 2


def _torch():
    import torch
    from torch import nn
    return torch, nn


def _encoder(nn, torch, n_features: int, seq_len: int, cfg: ContextualConfig):
    """A small transformer encoder -> last-step summary vector (B, d_model)."""
    class Enc(nn.Module):
        def __init__(self):
            super().__init__()
            self.proj = nn.Linear(n_features, cfg.d_model)
            self.pos = nn.Parameter(torch.zeros(1, seq_len, cfg.d_model))
            layer = nn.TransformerEncoderLayer(
                d_model=cfg.d_model, nhead=cfg.n_heads, dim_feedforward=cfg.dim_ff,
                dropout=cfg.dropout, batch_first=True, activation="gelu")
            self.enc = nn.TransformerEncoder(layer, num_layers=cfg.n_layers)

        def forward(self, x):
            h = self.proj(x) + self.pos[:, : x.size(1)]
            return self.enc(h)[:, -1]   # last-step summary
    return Enc()


def build_model(cfg: ContextualConfig | None = None):
    torch, nn = _torch()
    cfg = cfg or ContextualConfig()

    class Contextual(nn.Module):
        def __init__(self, c: ContextualConfig):
            super().__init__()
            self.c = c
            self.price_enc = _encoder(nn, torch, c.price_feats, c.price_seq, c)
            self.macro_enc = _encoder(nn, torch, c.macro_feats, c.macro_seq, c)
            self.asset_emb = nn.Embedding(c.n_assets, c.d_model)
            self.trunk = nn.Sequential(
                nn.LayerNorm(c.d_model * 2),
                nn.Linear(c.d_model * 2, c.d_model), nn.GELU(), nn.Dropout(c.dropout),
            )
            self.heads = nn.ModuleDict({h: nn.Linear(c.d_model, c.n_classes) for h in HORIZONS})

        def forward(self, price_x, macro_x, asset_id):
            p = self.price_enc(price_x) + self.asset_emb(asset_id)
            if macro_x is None:                       # graceful: no macro -> zeros
                m = torch.zeros_like(p)
            else:
                m = self.macro_enc(macro_x)
            z = self.trunk(torch.cat([p, m], dim=-1))
            return {h: self.heads[h](z) for h in HORIZONS}

    return Contextual(cfg)


# ---- normalization (fit on train only, stored in checkpoint) ----------------

def fit_norm(price_X: np.ndarray, macro_X: np.ndarray) -> dict:
    return {
        "price_mean": price_X.reshape(-1, price_X.shape[-1]).mean(0).tolist(),
        "price_std": (price_X.reshape(-1, price_X.shape[-1]).std(0) + 1e-6).tolist(),
        "macro_mean": macro_X.reshape(-1, macro_X.shape[-1]).mean(0).tolist(),
        "macro_std": (macro_X.reshape(-1, macro_X.shape[-1]).std(0) + 1e-6).tolist(),
    }


def apply_norm(price_X: np.ndarray, macro_X: np.ndarray, norm: dict) -> tuple[np.ndarray, np.ndarray]:
    px = (price_X - np.asarray(norm["price_mean"])) / np.asarray(norm["price_std"])
    mx = (macro_X - np.asarray(norm["macro_mean"])) / np.asarray(norm["macro_std"])
    return px.astype(np.float32), mx.astype(np.float32)


# ---- inference --------------------------------------------------------------

def predict(model, price_X: np.ndarray, macro_X: np.ndarray, asset_id: np.ndarray,
            batch_size: int = 256) -> dict[str, np.ndarray]:
    """Return {horizon: (N,3) softmax} for the given (already-normalized) inputs."""
    torch, _ = _torch()
    model.eval()
    out = {h: [] for h in HORIZONS}
    with torch.no_grad():
        for i in range(0, len(price_X), batch_size):
            px = torch.from_numpy(price_X[i:i + batch_size]).float()
            mx = torch.from_numpy(macro_X[i:i + batch_size]).float()
            aid = torch.from_numpy(asset_id[i:i + batch_size]).long()
            logits = model(px, mx, aid)
            for h in HORIZONS:
                out[h].append(torch.softmax(logits[h], -1).cpu().numpy())
    return {h: (np.concatenate(v) if v else np.empty((0, 3))) for h, v in out.items()}


def proba_to_forecast(proba: np.ndarray, min_conf: float = 0.0) -> tuple[str, float]:
    """Single (3,) proba -> (direction, confidence) — margin over uniform, scaled to [0,1]."""
    top = int(np.argmax(proba))
    conf = max(0.0, min(1.0, float((proba[top] - 1 / 3) / (2 / 3))))
    return (("flat", conf) if conf < min_conf else (CLASSES[top], conf))


# ---- regime readout (transparent rule over the macro panel) -----------------

def regime_readout(macro_row: dict) -> dict:
    """Map the latest macro row -> a human-readable regime. Transparent by design.

    Liquidity expanding (net-liq rising + M2 growing) and a non-surging dollar =>
    risk-on/EXPANDING; the opposite => CONTRACTING; mixed => NEUTRAL.
    """
    netliq = float(macro_row.get("netliq_chg4w", 0.0))
    m2 = float(macro_row.get("m2_yoy", 0.0))
    dxy = float(macro_row.get("dxy_chg4w", 0.0))
    score = np.sign(netliq) + np.sign(m2) - np.sign(dxy)   # in [-3, 3]
    label = "EXPANDING" if score >= 2 else "CONTRACTING" if score <= -2 else "NEUTRAL"
    return {
        "regime": label,
        "score": int(score),
        "drivers": {"netliq_chg4w": round(netliq, 4), "m2_yoy": round(m2, 4),
                    "dxy_chg4w": round(dxy, 4)},
    }
