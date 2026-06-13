from __future__ import annotations

import os

from deepCommodity.execution._valuation import value_crypto_balances
from deepCommodity.execution.broker import BrokerAdapter, OrderRequest, OrderResult
from deepCommodity.util import envbool


def _binance_use_sandbox(mode: str) -> bool:
    """Sandbox unless we are explicitly in live mode AND testnet is explicitly off.

    Defaults fail safe: paper mode always sandboxes; a missing/whitespace
    BINANCE_TESTNET keeps us on testnet.
    """
    return mode != "live" or envbool("BINANCE_TESTNET", True)


class BinanceAdapter(BrokerAdapter):
    name = "binance"

    def __init__(self) -> None:
        try:
            import ccxt  # type: ignore
        except ImportError as e:
            raise RuntimeError("ccxt not installed; pip install ccxt") from e
        self._ccxt = ccxt
        self._client = self._make_client()

    def _make_client(self):
        cfg = {
            "apiKey": os.getenv("BINANCE_API_KEY", ""),
            "secret": os.getenv("BINANCE_API_SECRET", ""),
            "enableRateLimit": True,
        }
        client = self._ccxt.binance(cfg)
        if _binance_use_sandbox(self.mode):
            client.set_sandbox_mode(True)
        return client

    @staticmethod
    def _to_pair(symbol: str) -> str:
        return symbol if "/" in symbol else f"{symbol.upper()}/USDT"

    def submit(self, req: OrderRequest) -> OrderResult:
        pair = self._to_pair(req.symbol)
        try:
            # round qty DOWN to the exchange step size so we never exceed the sized notional
            qty = float(self._client.amount_to_precision(pair, req.qty))
            if qty <= 0:
                return OrderResult(
                    ok=False, broker=self.name, mode=self.mode,
                    symbol=req.symbol, side=req.side, qty=req.qty,
                    error="qty rounds to zero at exchange precision",
                )
            params = {}
            if req.client_order_id:
                params["clientOrderId"] = req.client_order_id
            if req.type == "market":
                order = self._client.create_order(pair, "market", req.side, qty, None, params)
            else:
                order = self._client.create_order(
                    pair, "limit", req.side, qty, req.limit_price, params
                )
            return OrderResult(
                ok=True,
                broker=self.name,
                mode=self.mode,
                symbol=req.symbol,
                side=req.side,
                qty=qty,
                fill_price=order.get("average") or order.get("price"),
                order_id=str(order.get("id")),
                raw=order,
            )
        except Exception as e:  # noqa: BLE001
            return OrderResult(
                ok=False, broker=self.name, mode=self.mode,
                symbol=req.symbol, side=req.side, qty=req.qty, error=str(e),
            )

    def account_state(self) -> tuple[float, dict[str, float], float]:
        bal = self._client.fetch_balance()
        totals = bal.get("total", {}) or {}
        free = bal.get("free", {}) or {}
        tickers = self._client.fetch_tickers()
        return value_crypto_balances(totals, free, tickers)

    def reference_price(self, symbol: str) -> float:
        t = self._client.fetch_ticker(self._to_pair(symbol))
        px = t.get("last") or t.get("close")
        if not px:
            raise RuntimeError(f"no reference price for {symbol}")
        return float(px)
