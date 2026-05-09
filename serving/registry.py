"""Model registry: loads checkpoints from disk into memory at startup, supports
hot-reload, and exposes typed accessors per modality.

Layout convention:
    $MODELS_DIR/<SYMBOL>.pt              - price transformer
    $MODELS_DIR/<SYMBOL>.orderflow.pt    - order-flow transformer
    $MODELS_DIR/fused/<SYMBOL>.pt        - fused multi-modal (optional)

Models are immutable in memory once loaded; reload swaps the entire registry
atomically so in-flight requests see a consistent snapshot.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("dc-serve.registry")


@dataclass
class LoadedModel:
    symbol: str
    kind: str                      # "price" | "orderflow" | "fused"
    path: Path
    config: dict
    handle: Any                    # torch.nn.Module
    loaded_at: float = field(default_factory=time.time)


class ModelRegistry:
    def __init__(self, models_dir: Path):
        self.models_dir = Path(models_dir)
        self._lock = threading.RLock()
        self._models: dict[tuple[str, str], LoadedModel] = {}

    def load_all(self) -> dict[str, list[str]]:
        """Load every checkpoint under models_dir. Returns {kind: [symbols]}."""
        try:
            import torch
        except ImportError:
            log.warning("torch not installed; registry will only serve rule-based + news")
            return {}

        from deepCommodity.model.price_transformer import (
            TransformerConfig as PriceCfg,
            build_model as build_price,
        )
        from deepCommodity.model.orderflow_transformer import (
            OrderflowConfig as OFCfg,
            build_model as build_of,
        )

        new_models: dict[tuple[str, str], LoadedModel] = {}

        if not self.models_dir.exists():
            log.warning("models dir %s does not exist; serving without models", self.models_dir)
        else:
            for f in sorted(self.models_dir.glob("*.pt")):
                try:
                    if ".orderflow" in f.name:
                        sym = f.name.replace(".orderflow.pt", "").upper()
                        ckpt = torch.load(f, map_location="cpu")
                        cfg = OFCfg(**ckpt["config"])
                        m = build_of(cfg)
                        m.load_state_dict(ckpt["state_dict"])
                        m.eval()
                        new_models[(sym, "orderflow")] = LoadedModel(
                            symbol=sym, kind="orderflow", path=f,
                            config=ckpt["config"], handle=m,
                        )
                    else:
                        sym = f.stem.upper()
                        ckpt = torch.load(f, map_location="cpu")
                        cfg = PriceCfg(**ckpt["config"])
                        m = build_price(cfg)
                        m.load_state_dict(ckpt["state_dict"])
                        m.eval()
                        new_models[(sym, "price")] = LoadedModel(
                            symbol=sym, kind="price", path=f,
                            config=ckpt["config"], handle=m,
                        )
                except Exception as e:  # noqa: BLE001
                    log.error("failed to load %s: %s", f, e)

        with self._lock:
            self._models = new_models

        summary: dict[str, list[str]] = {}
        for (sym, kind) in new_models:
            summary.setdefault(kind, []).append(sym)
        log.info("registry loaded: %s", summary)
        return summary

    def get(self, symbol: str, kind: str) -> LoadedModel | None:
        with self._lock:
            return self._models.get((symbol.upper(), kind))

    def list_available(self) -> dict[str, list[str]]:
        with self._lock:
            out: dict[str, list[str]] = {}
            for (sym, kind) in self._models:
                out.setdefault(kind, []).append(sym)
            return out


def get_models_dir() -> Path:
    return Path(os.getenv("MODELS_DIR", "/srv/models"))
