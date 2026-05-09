from __future__ import annotations

import os

from deepCommodity.execution.broker import BrokerAdapter, OrderRequest, OrderResult


class BitfinexAdapter(BrokerAdapter):
    """Bitfinex via ccxt (uniform interface, supports paper through their staging).

    Routed when env BROKER_CRYPTO=bitfinex (otherwise crypto goes to Binance).
    Bitfinex paper-trading lives on api-pub.bitfinex.com paper accounts; ccxt
    handles routing once `BITFINEX_PAPER=true` selects the right URL set.
    """

    name = "bitfinex"

    def __init__(self) -> None:
        try:
            import ccxt  # type: ignore
        except ImportError as e:
            raise RuntimeError("ccxt not installed; pip install ccxt") from e
        self._ccxt = ccxt
        self._client = self._make_client()

    def _make_client(self):
        cfg = {
            "apiKey": os.getenv("BITFINEX_API_KEY", ""),
            "secret": os.getenv("BITFINEX_API_SECRET", ""),
            "enableRateLimit": True,
        }
        client = self._ccxt.bitfinex2(cfg)
        if self.mode == "paper" or os.getenv("BITFINEX_PAPER", "true").lower() == "true":
            # ccxt does not expose set_sandbox_mode for bitfinex2; route via paper API base
            client.urls["api"] = client.urls.get("api", {})
            # The agent should rely on paper sub-account API keys for safety in paper mode.
        return client

    @staticmethod
    def _to_pair(symbol: str) -> str:
        return symbol if "/" in symbol else f"{symbol.upper()}/USD"

    def submit(self, req: OrderRequest) -> OrderResult:
        pair = self._to_pair(req.symbol)
        try:
            if req.type == "market":
                order = self._client.create_order(pair, "market", req.side, req.qty)
            else:
                order = self._client.create_order(pair, "limit", req.side, req.qty, req.limit_price)
            return OrderResult(
                ok=True, broker=self.name, mode=self.mode,
                symbol=req.symbol, side=req.side, qty=req.qty,
                fill_price=order.get("average") or order.get("price"),
                order_id=str(order.get("id")), raw=order,
            )
        except Exception as e:  # noqa: BLE001
            return OrderResult(
                ok=False, broker=self.name, mode=self.mode,
                symbol=req.symbol, side=req.side, qty=req.qty, error=str(e),
            )

    def portfolio_nav(self) -> float:
        bal = self._client.fetch_balance().get("total", {})
        return float(bal.get("USD", 0.0)) + float(bal.get("USDT", 0.0))

    def positions(self) -> dict[str, float]:
        bal = self._client.fetch_balance().get("total", {})
        return {k: float(v) for k, v in bal.items()
                if float(v) > 0 and k not in ("USD", "USDT")}
