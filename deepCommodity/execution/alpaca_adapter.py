from __future__ import annotations

import os

from deepCommodity.execution.broker import BrokerAdapter, OrderRequest, OrderResult


class AlpacaAdapter(BrokerAdapter):
    name = "alpaca"

    def __init__(self) -> None:
        try:
            from alpaca.trading.client import TradingClient  # type: ignore
            from alpaca.trading.requests import (
                LimitOrderRequest,
                MarketOrderRequest,
            )  # type: ignore
            from alpaca.trading.enums import OrderSide, TimeInForce  # type: ignore
        except ImportError as e:
            raise RuntimeError("alpaca-py not installed; pip install alpaca-py") from e
        self._MarketOrderRequest = MarketOrderRequest
        self._LimitOrderRequest = LimitOrderRequest
        self._OrderSide = OrderSide
        self._TimeInForce = TimeInForce
        paper = os.getenv("ALPACA_PAPER", "true").lower() == "true" or self.mode == "paper"
        self._client = TradingClient(
            api_key=os.getenv("ALPACA_API_KEY", ""),
            secret_key=os.getenv("ALPACA_API_SECRET", ""),
            paper=paper,
        )

    def submit(self, req: OrderRequest) -> OrderResult:
        side = self._OrderSide.BUY if req.side == "buy" else self._OrderSide.SELL
        try:
            if req.type == "market":
                order_req = self._MarketOrderRequest(
                    symbol=req.symbol, qty=req.qty, side=side,
                    time_in_force=self._TimeInForce.DAY,
                )
            else:
                order_req = self._LimitOrderRequest(
                    symbol=req.symbol, qty=req.qty, side=side,
                    time_in_force=self._TimeInForce.DAY,
                    limit_price=req.limit_price,
                )
            order = self._client.submit_order(order_req)
            return OrderResult(
                ok=True,
                broker=self.name,
                mode=self.mode,
                symbol=req.symbol,
                side=req.side,
                qty=req.qty,
                fill_price=float(getattr(order, "filled_avg_price", 0) or 0) or None,
                order_id=str(order.id),
                raw=order.__dict__ if hasattr(order, "__dict__") else {},
            )
        except Exception as e:  # noqa: BLE001
            return OrderResult(
                ok=False, broker=self.name, mode=self.mode,
                symbol=req.symbol, side=req.side, qty=req.qty, error=str(e),
            )

    def portfolio_nav(self) -> float:
        acct = self._client.get_account()
        return float(acct.equity)

    def positions(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for p in self._client.get_all_positions():
            out[p.symbol] = float(p.market_value)
        return out
