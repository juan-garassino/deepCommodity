from __future__ import annotations

import os

from deepCommodity.execution._valuation import value_crypto_balances
from deepCommodity.execution.broker import BrokerAdapter, OrderRequest, OrderResult
from deepCommodity.util import envbool


class BitfinexAdapter(BrokerAdapter):
    """Bitfinex via ccxt — DISABLED in the live path (audit fix B7).

    ccxt's bitfinex2 has no real sandbox routing, so "paper mode" here previously
    sent live orders to whatever account the keys belonged to. The adapter now
    refuses to construct unless the operator has explicitly confirmed they have
    verified paper sub-account keys (BITFINEX_SANDBOX_CONFIRMED=true). Until real
    sandbox routing exists, crypto goes to Binance.
    """

    name = "bitfinex"

    def __init__(self) -> None:
        if not envbool("BITFINEX_SANDBOX_CONFIRMED", False):
            raise RuntimeError(
                "Bitfinex adapter disabled: no verified paper routing (audit B7). "
                "Use Binance for crypto, or set BITFINEX_SANDBOX_CONFIRMED=true only if "
                "you have confirmed paper sub-account keys."
            )
        try:
            import ccxt  # type: ignore
        except ImportError as e:
            raise RuntimeError("ccxt not installed; pip install ccxt") from e
        self._ccxt = ccxt
        self._client = self._ccxt.bitfinex2({
            "apiKey": os.getenv("BITFINEX_API_KEY", ""),
            "secret": os.getenv("BITFINEX_API_SECRET", ""),
            "enableRateLimit": True,
        })

    @staticmethod
    def _to_pair(symbol: str) -> str:
        return symbol if "/" in symbol else f"{symbol.upper()}/USD"

    def submit(self, req: OrderRequest) -> OrderResult:
        pair = self._to_pair(req.symbol)
        try:
            qty = float(self._client.amount_to_precision(pair, req.qty))
            if qty <= 0:
                return OrderResult(
                    ok=False, broker=self.name, mode=self.mode,
                    symbol=req.symbol, side=req.side, qty=req.qty,
                    error="qty rounds to zero at exchange precision",
                )
            params = {"clientOrderId": req.client_order_id} if req.client_order_id else {}
            otype = "market" if req.type == "market" else "limit"
            price = None if req.type == "market" else req.limit_price
            order = self._client.create_order(pair, otype, req.side, qty, price, params)
            return OrderResult(
                ok=True, broker=self.name, mode=self.mode,
                symbol=req.symbol, side=req.side, qty=qty,
                fill_price=order.get("average") or order.get("price"),
                order_id=str(order.get("id")), raw=order,
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
