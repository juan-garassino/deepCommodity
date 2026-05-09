from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

Side = Literal["buy", "sell"]
AssetClass = Literal["crypto", "equity"]


@dataclass
class OrderRequest:
    symbol: str
    side: Side
    qty: float
    asset_class: AssetClass
    type: Literal["market", "limit"] = "market"
    limit_price: float | None = None
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None


@dataclass
class OrderResult:
    ok: bool
    broker: str
    mode: str                 # "paper" | "live"
    symbol: str
    side: Side
    qty: float
    fill_price: float | None = None
    order_id: str | None = None
    raw: dict = field(default_factory=dict)
    error: str | None = None


class BrokerAdapter(ABC):
    name: str = "abstract"

    @property
    def mode(self) -> str:
        return os.getenv("TRADING_MODE", "paper").lower()

    @abstractmethod
    def submit(self, req: OrderRequest) -> OrderResult: ...

    @abstractmethod
    def portfolio_nav(self) -> float: ...

    @abstractmethod
    def positions(self) -> dict[str, float]: ...


def get_broker(asset_class: AssetClass) -> BrokerAdapter:
    if asset_class == "crypto":
        venue = os.getenv("BROKER_CRYPTO", "binance").lower()
        if venue == "bitfinex":
            from deepCommodity.execution.bitfinex_adapter import BitfinexAdapter
            return BitfinexAdapter()
        from deepCommodity.execution.binance_adapter import BinanceAdapter
        return BinanceAdapter()
    if asset_class == "equity":
        from deepCommodity.execution.alpaca_adapter import AlpacaAdapter
        return AlpacaAdapter()
    raise ValueError(f"unknown asset_class: {asset_class}")
