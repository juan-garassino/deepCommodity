"""Hand-rolled broker/portfolio mocks (no Mock library — repo convention).

Used to exercise the order-submission path and gate logic without a live broker.
"""
from __future__ import annotations

from deepCommodity.execution.broker import BrokerAdapter, OrderRequest, OrderResult
from deepCommodity.execution.portfolio import MockPortfolioProvider, PortfolioUnavailable
from deepCommodity.guardrails.limits import PortfolioSnapshot


class MockBroker(BrokerAdapter):
    """Records submitted OrderRequests; returns a configurable result."""

    name = "mock"

    def __init__(self, *, nav=10_000.0, positions=None, cash=10_000.0,
                 ref_price=100.0, ok=True, fill_price=123.0, error=None,
                 raise_on_state=False, ref_raise=False):
        self._nav = nav
        self._positions = positions or {}
        self._cash = cash
        self._ref_price = ref_price
        self._ok = ok
        self._fill_price = fill_price
        self._error = error
        self._raise_on_state = raise_on_state
        self._ref_raise = ref_raise
        self.calls: list[OrderRequest] = []

    def submit(self, req: OrderRequest) -> OrderResult:
        self.calls.append(req)
        return OrderResult(
            ok=self._ok, broker=self.name, mode=self.mode,
            symbol=req.symbol, side=req.side, qty=req.qty,
            fill_price=self._fill_price if self._ok else None,
            order_id="mock-1" if self._ok else None,
            error=self._error if not self._ok else None,
        )

    def account_state(self):
        if self._raise_on_state:
            raise RuntimeError("mock broker state unavailable")
        return self._nav, self._positions, self._cash

    def reference_price(self, symbol: str) -> float:
        if self._ref_raise:
            raise RuntimeError("no quote")
        return self._ref_price


def make_snapshot(nav=10_000.0, cash=10_000.0, positions=None,
                  sector_notional=None, new_positions_today=None) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        nav_usd=nav, cash_usd=cash, positions=positions or {},
        sector_notional=sector_notional or {},
        new_positions_today=new_positions_today or {},
    )


def provider_for(**kw) -> MockPortfolioProvider:
    return MockPortfolioProvider(snapshot=make_snapshot(**kw))


__all__ = ["MockBroker", "make_snapshot", "provider_for",
           "MockPortfolioProvider", "PortfolioUnavailable"]
