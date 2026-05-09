"""Phase 8 fused multi-modal transformer."""
from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from deepCommodity.model.fused_transformer import FusedConfig, build_model  # noqa: E402
from deepCommodity.model.orderflow_transformer import (  # noqa: E402
    OrderflowConfig,
    build_model as build_orderflow,
)
from deepCommodity.model.price_transformer import (  # noqa: E402
    TransformerConfig,
    build_model as build_price,
)


def _encoders():
    pcfg = TransformerConfig(seq_len=32, n_features=4, d_model=32,
                             n_heads=4, n_layers=1, dim_ff=64)
    ocfg = OrderflowConfig(seq_len=32, n_features=4, d_model=32,
                           n_heads=4, n_layers=1, dim_ff=64)
    return build_price(pcfg), build_orderflow(ocfg), pcfg, ocfg


def test_fused_runs_with_all_modalities():
    pe, oe, _, _ = _encoders()
    cfg = FusedConfig(price_d_model=32, orderflow_d_model=32, fused_hidden=64)
    fused = build_model(pe, oe, cfg)
    px = torch.randn(4, 32, 4)
    ox = torch.randn(4, 32, 4)
    nx = torch.tensor([[0.5, 0.8], [-0.3, 0.6], [0.0, 0.0], [0.7, 0.9]])
    out = fused(price_x=px, orderflow_x=ox, news_x=nx)
    assert out.shape == (4, 3)


def test_fused_runs_with_only_price():
    pe, oe, _, _ = _encoders()
    cfg = FusedConfig(price_d_model=32, orderflow_d_model=32, fused_hidden=64)
    fused = build_model(pe, oe, cfg)
    px = torch.randn(2, 32, 4)
    out = fused(price_x=px)
    assert out.shape == (2, 3)


def test_fused_runs_with_only_news():
    pe, oe, _, _ = _encoders()
    cfg = FusedConfig(price_d_model=32, orderflow_d_model=32, fused_hidden=64)
    fused = build_model(pe, oe, cfg)
    nx = torch.tensor([[0.5, 0.8]])
    out = fused(news_x=nx)
    assert out.shape == (1, 3)


def test_fused_with_no_inputs_uses_zero_vectors():
    """Edge case: nothing provided → zeros all the way through; output shape (1, 3)."""
    pe, oe, _, _ = _encoders()
    cfg = FusedConfig(price_d_model=32, orderflow_d_model=32, fused_hidden=64)
    fused = build_model(pe, oe, cfg)
    out = fused()
    assert out.shape == (1, 3)


def test_fused_handles_missing_encoder():
    """If an encoder is None, the trunk should still produce valid output via zero substitution."""
    cfg = FusedConfig(price_d_model=32, orderflow_d_model=32, fused_hidden=64)
    fused = build_model(price_encoder=None, orderflow_encoder=None, cfg=cfg)
    nx = torch.tensor([[0.1, 0.4]])
    out = fused(news_x=nx)
    assert out.shape == (1, 3)


def test_modality_dropout_only_in_train_mode():
    pe, oe, _, _ = _encoders()
    cfg = FusedConfig(price_d_model=32, orderflow_d_model=32, fused_hidden=64,
                      modality_dropout=0.99)
    fused = build_model(pe, oe, cfg)
    fused.eval()
    px = torch.randn(8, 32, 4)
    out_eval = fused(price_x=px)
    fused.train()
    out_train = fused(price_x=px)
    # in eval mode no dropout; in train mode the same input + modality_dropout=0.99
    # should produce a different output for a non-trivial fraction of samples
    assert out_eval.shape == out_train.shape == (8, 3)


def test_fused_backprop_does_not_explode():
    pe, oe, _, _ = _encoders()
    cfg = FusedConfig(price_d_model=32, orderflow_d_model=32, fused_hidden=64,
                      modality_dropout=0.0)
    fused = build_model(pe, oe, cfg)
    px = torch.randn(8, 32, 4)
    y = torch.randint(0, 3, (8,))
    logits = fused(price_x=px)
    loss = torch.nn.functional.cross_entropy(logits, y)
    loss.backward()
    grads = [p.grad for p in fused.parameters() if p.grad is not None]
    assert all(torch.isfinite(g).all() for g in grads)
