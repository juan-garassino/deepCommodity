from __future__ import annotations

import os

from deepCommodity.execution.broker import BrokerAdapter, OrderRequest, OrderResult


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
        # Testnet routing when paper or BINANCE_TESTNET=true
        if self.mode == "paper" or os.getenv("BINANCE_TESTNET", "true").lower() == "true":
            client.set_sandbox_mode(True)
        return client

    @staticmethod
    def _to_pair(symbol: str) -> str:
        return symbol if "/" in symbol else f"{symbol.upper()}/USDT"

    def submit(self, req: OrderRequest) -> OrderResult:
        pair = self._to_pair(req.symbol)
        try:
            if req.type == "market":
                order = self._client.create_order(pair, "market", req.side, req.qty)
            else:
                order = self._client.create_order(
                    pair, "limit", req.side, req.qty, req.limit_price
                )
            return OrderResult(
                ok=True,
                broker=self.name,
                mode=self.mode,
                symbol=req.symbol,
                side=req.side,
                qty=req.qty,
                fill_price=order.get("average") or order.get("price"),
                order_id=str(order.get("id")),
                raw=order,
            )
        except Exception as e:  # noqa: BLE001
            return OrderResult(
                ok=False, broker=self.name, mode=self.mode,
                symbol=req.symbol, side=req.side, qty=req.qty, error=str(e),
            )

    def portfolio_nav(self) -> float:
        bal = self._client.fetch_balance()
        # USDT-equivalent NAV approximation (testnet/live both expose total in 'total')
        total = bal.get("total", {})
        usdt = float(total.get("USDT", 0.0))
        # naive: treat non-USDT balances as zero in v1; real NAV computed via tickers later
        return usdt

    def positions(self) -> dict[str, float]:
        bal = self._client.fetch_balance().get("total", {})
        return {k: float(v) for k, v in bal.items() if float(v) > 0 and k != "USDT"}
