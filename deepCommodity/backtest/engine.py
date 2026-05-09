"""Walk-forward backtest engine.

Inputs
------
* `bars`     : per-symbol price history, dict[symbol] -> list[Bar(ts, close)]
               (richer schemas welcome — close is the only required field).
* `forecaster`: callable(window: dict[symbol, list[Bar]]) -> list[Forecast].
                Phase 1 wires this to the rule-based forecaster. Phase 5+
                drops in the price transformer; same interface.
* `config`   : starting NAV, position cap, risk-check on/off, transaction
               cost in bps, slippage in bps, etc.

The engine is deliberately broker-agnostic — no Binance/Alpaca calls. It uses
`PaperBook` to track an in-memory portfolio against the same `check_limits`
the live path enforces, so the backtest's risk gating is identical to prod.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Iterable

from deepCommodity.guardrails.limits import (
    OrderProposal,
    PortfolioSnapshot,
    check_limits,
)


@dataclass(frozen=True)
class Bar:
    ts: datetime
    close: float
    volume: float = 0.0


@dataclass
class Forecast:
    symbol: str
    direction: str            # "long" | "short" | "flat"
    confidence: float


@dataclass
class BacktestConfig:
    starting_nav: float = 10_000.0
    transaction_cost_bps: float = 5.0          # 0.05% each side
    slippage_bps: float = 2.0
    min_confidence: float = 0.60
    position_pct: float = 0.05                  # of NAV per new position
    enforce_risk_check: bool = True
    rebalance_every: int = 1                    # bars between forecast calls
    warmup_bars: int = 60                       # bars before first trade


@dataclass
class Trade:
    ts: datetime
    symbol: str
    side: str
    qty: float
    price: float
    notional: float
    cost: float


@dataclass
class BacktestResult:
    final_nav: float
    return_pct: float
    sharpe: float
    max_drawdown: float
    n_trades: int
    n_blocked: int
    win_rate: float
    trades: list[Trade]
    nav_curve: list[tuple[datetime, float]]


class PaperBook:
    def __init__(self, cfg: BacktestConfig):
        self.cfg = cfg
        self.cash = cfg.starting_nav
        # symbol -> (qty, avg_entry_price)
        self.positions: dict[str, tuple[float, float]] = {}
        self.trades: list[Trade] = []
        self.blocked = 0
        self.new_positions_today = 0

    def mark_to_market(self, prices: dict[str, float]) -> float:
        eq = self.cash
        for sym, (qty, _) in self.positions.items():
            if sym in prices:
                eq += qty * prices[sym]
        return eq

    def snapshot(self, prices: dict[str, float]) -> PortfolioSnapshot:
        nav = self.mark_to_market(prices)
        notional = {s: qty * prices.get(s, p) for s, (qty, p) in self.positions.items()}
        return PortfolioSnapshot(
            nav_usd=nav, cash_usd=self.cash, positions=notional,
            sector_notional={}, new_positions_today=self.new_positions_today,
        )

    def submit(self, ts: datetime, symbol: str, side: str, qty: float,
               price: float) -> bool:
        slip = self.cfg.slippage_bps / 10_000
        fill = price * (1 + slip if side == "buy" else 1 - slip)
        notional = qty * fill
        cost = notional * (self.cfg.transaction_cost_bps / 10_000)

        if side == "buy":
            if self.cash < notional + cost:
                self.blocked += 1
                return False
            held_qty, avg = self.positions.get(symbol, (0.0, 0.0))
            new_qty = held_qty + qty
            new_avg = (held_qty * avg + qty * fill) / new_qty if new_qty else 0.0
            self.positions[symbol] = (new_qty, new_avg)
            self.cash -= notional + cost
            if held_qty == 0:
                self.new_positions_today += 1
        else:  # sell
            held_qty, avg = self.positions.get(symbol, (0.0, 0.0))
            if held_qty < qty:
                self.blocked += 1
                return False
            new_qty = held_qty - qty
            self.positions[symbol] = (new_qty, avg) if new_qty > 0 else (0.0, 0.0)
            if new_qty == 0:
                self.positions.pop(symbol)
            self.cash += notional - cost

        self.trades.append(
            Trade(ts=ts, symbol=symbol, side=side, qty=qty,
                  price=fill, notional=notional, cost=cost)
        )
        return True


def _max_drawdown(nav_curve: list[tuple[datetime, float]]) -> float:
    peak = -math.inf
    mdd = 0.0
    for _, v in nav_curve:
        peak = max(peak, v)
        if peak > 0:
            mdd = min(mdd, (v - peak) / peak)
    return mdd


def _sharpe(returns: list[float], periods_per_year: int = 252) -> float:
    if len(returns) < 2:
        return 0.0
    sd = statistics.pstdev(returns)
    if sd == 0:
        return 0.0
    return (statistics.mean(returns) / sd) * math.sqrt(periods_per_year)


def _hit_rate(book: PaperBook) -> float:
    """Round-trip win rate: pair each sell with the most recent buy of the same symbol."""
    wins = total = 0
    open_legs: dict[str, list[Trade]] = {}
    for t in book.trades:
        if t.side == "buy":
            open_legs.setdefault(t.symbol, []).append(t)
        else:
            stack = open_legs.get(t.symbol, [])
            if not stack:
                continue
            entry = stack.pop()
            total += 1
            if t.price > entry.price:
                wins += 1
    return wins / total if total else 0.0


def run_backtest(
    bars: dict[str, list[Bar]],
    forecaster: Callable[[dict[str, list[Bar]]], list[Forecast]],
    config: BacktestConfig | None = None,
) -> BacktestResult:
    cfg = config or BacktestConfig()
    book = PaperBook(cfg)

    # Walk by index; assume per-symbol bars share length & timestamps for v1.
    symbols = list(bars.keys())
    n = min(len(bars[s]) for s in symbols)
    if n <= cfg.warmup_bars:
        raise ValueError(f"need > {cfg.warmup_bars} bars (got {n})")

    nav_curve: list[tuple[datetime, float]] = []
    last_nav = cfg.starting_nav
    returns: list[float] = []

    prev_day: int | None = None
    for i in range(cfg.warmup_bars, n):
        ts = bars[symbols[0]][i].ts
        prices = {s: bars[s][i].close for s in symbols}

        # reset new-position counter each calendar day
        day = ts.toordinal()
        if prev_day is not None and day != prev_day:
            book.new_positions_today = 0
        prev_day = day

        if (i - cfg.warmup_bars) % cfg.rebalance_every == 0:
            window = {s: bars[s][:i+1] for s in symbols}
            forecasts = forecaster(window)
            for f in forecasts:
                if f.confidence < cfg.min_confidence:
                    continue
                px = prices.get(f.symbol)
                if px is None:
                    continue
                if f.direction == "long":
                    nav = book.mark_to_market(prices)
                    notional = nav * cfg.position_pct * min(1.0, f.confidence)
                    qty = notional / px
                    if cfg.enforce_risk_check:
                        proposal = OrderProposal(symbol=f.symbol, side="buy",
                                                 qty=qty, notional_usd=notional)
                        ok, _ = check_limits(proposal, book.snapshot(prices))
                        if not ok:
                            book.blocked += 1
                            continue
                    book.submit(ts, f.symbol, "buy", qty, px)
                elif f.direction == "short":
                    # v1: no shorts. Treat as exit-long if held.
                    held_qty, _ = book.positions.get(f.symbol, (0.0, 0.0))
                    if held_qty > 0:
                        book.submit(ts, f.symbol, "sell", held_qty, px)

        nav = book.mark_to_market(prices)
        nav_curve.append((ts, nav))
        if last_nav > 0:
            returns.append((nav - last_nav) / last_nav)
        last_nav = nav

    final_nav = nav_curve[-1][1] if nav_curve else cfg.starting_nav
    return BacktestResult(
        final_nav=final_nav,
        return_pct=(final_nav - cfg.starting_nav) / cfg.starting_nav,
        sharpe=_sharpe(returns),
        max_drawdown=_max_drawdown(nav_curve),
        n_trades=len(book.trades),
        n_blocked=book.blocked,
        win_rate=_hit_rate(book),
        trades=book.trades,
        nav_curve=nav_curve,
    )
