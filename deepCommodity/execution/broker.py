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
    client_order_id: str | None = None


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

    # ---- normalized account state (all USD) --------------------------------
    # Implementations must raise on any failure — the caller fails closed.

    def account_state(self) -> tuple[float, dict[str, float], float]:
        """Return (nav_usd, positions_usd, cash_usd) from ONE consistent read.

        positions_usd is {symbol: USD notional}. Raise on any failure.
        """
        raise NotImplementedError

    def reference_price(self, symbol: str) -> float:
        """Current reference (mark/last) price in USD for sizing validation."""
        raise NotImplementedError


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
