"""Load named portfolios and blend the sleeves into price + carry weight panels."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

DEFAULT_YAML = Path(__file__).resolve().parent / "portfolios.yaml"


@dataclass
class PortfolioCfg:
    name: str
    blend: dict
    max_gross: float
    max_name: float
    vol_target: float
    de_lever_dd: float
    halt_dd: float
    long_only: bool = False


@dataclass
class Costs:
    taker_bps: float = 6.0
    borrow_bps_ann: float = 300.0


@dataclass
class PortfolioBook:
    cfgs: dict = field(default_factory=dict)
    costs: Costs = field(default_factory=Costs)


def load_portfolios(path: Path = DEFAULT_YAML) -> PortfolioBook:
    raw = yaml.safe_load(Path(path).read_text())
    cfgs = {name: PortfolioCfg(name=name, blend=d["blend"], max_gross=d["max_gross"],
                               max_name=d["max_name"], vol_target=d["vol_target"],
                               de_lever_dd=d["de_lever_dd"], halt_dd=d["halt_dd"],
                               long_only=d.get("long_only", False))
            for name, d in raw["portfolios"].items()}
    return PortfolioBook(cfgs=cfgs, costs=Costs(**raw.get("costs", {})))


def build_weights(cfg: PortfolioCfg, xs_w: pd.DataFrame, carry_w: pd.DataFrame,
                  dir_w: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Blend sleeves -> (price_weights, carry_weights) panels (pre risk-overlay)."""
    b = cfg.blend
    price_w = b.get("xs", 0) * xs_w + b.get("dir", 0) * dir_w.reindex_like(xs_w).fillna(0.0)
    carry = b.get("carry", 0) * carry_w
    if cfg.long_only:
        price_w = price_w.clip(lower=0.0)
        carry = carry.clip(lower=0.0)
    return price_w.fillna(0.0), carry.fillna(0.0)
