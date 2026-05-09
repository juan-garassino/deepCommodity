"""Phase 8: fused multi-modal transformer.

Builds a shared prediction trunk on top of the Phase 5 / 6 / 7 specialist
encoders. Each modality stays first-class — its encoder weights are loaded
from the standalone checkpoint and can also be evaluated alone.

Design choice: simple gated concatenation fusion. Each modality emits a
`(d_model,)` summary; we concat available modalities and feed through a
2-layer MLP to produce direction logits. Modality-dropout during training
makes the model robust to a missing input stream at inference (e.g. order
flow stale during low-volume hours).

Inference contract:
    fused_predict(modalities: dict[str, torch.Tensor]) -> proba (3,)
where keys are any subset of {"price", "orderflow", "news"}.

The "news" branch ingests a sentiment vector `(value, confidence)` rather
than tokens — keeps the fused model lightweight and decouples it from the
text backend choice in news_model.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch  # noqa: F401


def _torch():
    import torch
    from torch import nn
    return torch, nn


@dataclass
class FusedConfig:
    price_d_model: int = 64        # must match price_transformer cfg.d_model
    orderflow_d_model: int = 64
    news_dim: int = 2              # (sentiment_value, confidence)
    fused_hidden: int = 128
    n_classes: int = 3
    dropout: float = 0.1
    modality_dropout: float = 0.2  # train-time prob of zeroing a modality


def build_model(price_encoder, orderflow_encoder, cfg: FusedConfig | None = None):
    """Compose the fused trunk over pre-built specialist encoders.

    `price_encoder` / `orderflow_encoder` are torch.nn.Modules that expose
    `.encode(x) -> (B, T, d_model)`. Either may be None — the trunk handles
    missing modalities by zero-vector substitution.
    """
    torch, nn = _torch()
    cfg = cfg or FusedConfig()

    class FusedTransformer(nn.Module):
        def __init__(self):
            super().__init__()
            self.c = cfg
            self.price = price_encoder
            self.orderflow = orderflow_encoder
            in_dim = cfg.price_d_model + cfg.orderflow_d_model + cfg.news_dim
            self.trunk = nn.Sequential(
                nn.LayerNorm(in_dim),
                nn.Linear(in_dim, cfg.fused_hidden),
                nn.GELU(),
                nn.Dropout(cfg.dropout),
                nn.Linear(cfg.fused_hidden, cfg.fused_hidden),
                nn.GELU(),
                nn.Dropout(cfg.dropout),
                nn.Linear(cfg.fused_hidden, cfg.n_classes),
            )

        def _maybe_drop(self, vec, training: bool):
            if not training or cfg.modality_dropout <= 0:
                return vec
            mask = (torch.rand(vec.size(0), 1, device=vec.device) > cfg.modality_dropout).float()
            return vec * mask

        def forward(self,
                    price_x: "torch.Tensor | None" = None,
                    orderflow_x: "torch.Tensor | None" = None,
                    news_x: "torch.Tensor | None" = None) -> "torch.Tensor":
            # Determine batch size from any provided modality
            batch = next((t.size(0) for t in (price_x, orderflow_x, news_x) if t is not None), 1)
            device = next(self.parameters()).device

            if price_x is not None and self.price is not None:
                p = self.price.encode(price_x)[:, -1]   # (B, d_model)
            else:
                p = torch.zeros(batch, cfg.price_d_model, device=device)

            if orderflow_x is not None and self.orderflow is not None:
                o = self.orderflow.encode(orderflow_x)[:, -1]
            else:
                o = torch.zeros(batch, cfg.orderflow_d_model, device=device)

            if news_x is not None:
                n = news_x.float()
            else:
                n = torch.zeros(batch, cfg.news_dim, device=device)

            p = self._maybe_drop(p, self.training)
            o = self._maybe_drop(o, self.training)
            n = self._maybe_drop(n, self.training)

            return self.trunk(torch.cat([p, o, n], dim=-1))

    return FusedTransformer()


def fit_fused(model, batches, epochs: int = 10, lr: float = 3e-4, device: str | None = None):
    """Train the fused trunk (specialist encoders can be frozen via requires_grad=False).

    `batches` is an iterable of dicts with keys among
        {"price_x", "orderflow_x", "news_x", "y"}
    enabling pre-baked modality-availability patterns.
    """
    torch, nn = _torch()
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    history = {"loss": []}

    for ep in range(epochs):
        model.train()
        total = 0.0; n = 0
        for batch in batches:
            kwargs = {}
            for k in ("price_x", "orderflow_x", "news_x"):
                if k in batch and batch[k] is not None:
                    kwargs[k.replace("_x", "")] = batch[k].to(device) if hasattr(batch[k], "to") else batch[k]
            kwargs = {k + "_x": v for k, v in kwargs.items()}
            y = batch["y"].to(device)
            logits = model(**kwargs)
            loss = loss_fn(logits, y)
            opt.zero_grad(); loss.backward(); opt.step()
            total += loss.item() * y.size(0); n += y.size(0)
        history["loss"].append(total / max(1, n))
    return history
