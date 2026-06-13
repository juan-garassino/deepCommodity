from __future__ import annotations

import os
from datetime import datetime, timezone

from deepCommodity.execution.broker import BrokerAdapter, OrderRequest, OrderResult
from deepCommodity.util import envbool


def _alpaca_use_paper(mode: str) -> bool:
    """Paper unless live mode AND ALPACA_PAPER explicitly false.

    A live-mode run that did not explicitly opt out of paper is a misconfiguration
    (live intent, paper route/keys) — reject it rather than silently coerce.
    """
    if mode == "live":
        if envbool("ALPACA_PAPER", True):
            raise RuntimeError(
                "live mode requires ALPACA_PAPER=false explicitly (live uses a different keypair)"
            )
        return False
    return True


class AlpacaAdapter(BrokerAdapter):
    name = "alpaca"

    def __init__(self) -> None:
        try:
            from alpaca.trading.client import TradingClient  # type: ignore
            from alpaca.trading.requests import (
                GetOrdersRequest,
                LimitOrderRequest,
                MarketOrderRequest,
            )  # type: ignore
            from alpaca.trading.enums import (  # type: ignore
                OrderSide,
                QueryOrderStatus,
                TimeInForce,
            )
        except ImportError as e:
            raise RuntimeError("alpaca-py not installed; pip install alpaca-py") from e
        self._MarketOrderRequest = MarketOrderRequest
        self._LimitOrderRequest = LimitOrderRequest
        self._GetOrdersRequest = GetOrdersRequest
        self._OrderSide = OrderSide
        self._QueryOrderStatus = QueryOrderStatus
        self._TimeInForce = TimeInForce
        paper = _alpaca_use_paper(self.mode)
        self._client = TradingClient(
            api_key=os.getenv("ALPACA_API_KEY", ""),
            secret_key=os.getenv("ALPACA_API_SECRET", ""),
            paper=paper,
        )

    def submit(self, req: OrderRequest) -> OrderResult:
        side = self._OrderSide.BUY if req.side == "buy" else self._OrderSide.SELL
        try:
            kwargs = dict(
                symbol=req.symbol, qty=req.qty, side=side,
                time_in_force=self._TimeInForce.DAY,
            )
            if req.client_order_id:
                kwargs["client_order_id"] = req.client_order_id
            if req.type == "market":
                order_req = self._MarketOrderRequest(**kwargs)
            else:
                order_req = self._LimitOrderRequest(limit_price=req.limit_price, **kwargs)
            order = self._client.submit_order(order_req)
            fill_price = float(getattr(order, "filled_avg_price", 0) or 0) or None
            return OrderResult(
                ok=True,
                broker=self.name,
                mode=self.mode,
                symbol=req.symbol,
                side=req.side,
                qty=req.qty,
                fill_price=fill_price,
                order_id=str(order.id),
                raw=order.__dict__ if hasattr(order, "__dict__") else {},
            )
        except Exception as e:  # noqa: BLE001
            return OrderResult(
                ok=False, broker=self.name, mode=self.mode,
                symbol=req.symbol, side=req.side, qty=req.qty, error=str(e),
            )

    def account_state(self) -> tuple[float, dict[str, float], float]:
        acct = self._client.get_account()
        nav = float(acct.equity)
        cash = float(acct.cash)
        positions: dict[str, float] = {}
        for p in self._client.get_all_positions():
            positions[p.symbol] = float(p.market_value)
        return nav, positions, cash

    def reference_price(self, symbol: str) -> float:
        # Prefer a live quote from the (free IEX) data API so NEW symbols size off a
        # broker truth, not a trusted --price. Fall back to an open position's mark.
        try:
            from alpaca.data.historical import StockHistoricalDataClient  # type: ignore
            from alpaca.data.requests import StockLatestTradeRequest  # type: ignore

            data = StockHistoricalDataClient(
                api_key=os.getenv("ALPACA_API_KEY", ""),
                secret_key=os.getenv("ALPACA_API_SECRET", ""),
            )
            trade = data.get_stock_latest_trade(
                StockLatestTradeRequest(symbol_or_symbols=symbol)
            )
            px = float(trade[symbol].price)
            if px > 0:
                return px
        except Exception:  # noqa: BLE001 — fall back to held mark below
            pass
        for p in self._client.get_all_positions():
            if p.symbol == symbol and getattr(p, "current_price", None):
                return float(p.current_price)
        raise RuntimeError(f"no reference price for {symbol}")
