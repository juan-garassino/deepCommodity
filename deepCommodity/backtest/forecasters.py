"""Forecaster adapters that match the backtest engine's callable signature.

A forecaster is `(window: dict[symbol, list[Bar]]) -> list[Forecast]`.
"""
from __future__ import annotations

from deepCommodity.backtest.engine import Bar, Forecast


def _pct(a: float, b: float) -> float:
    return 0.0 if a == 0 else (b - a) / a * 100


def rule_based(window: dict[str, list[Bar]]) -> list[Forecast]:
    """The same logic as tools/forecast.py, applied to historical bars.

    Uses the last bar's close vs 1d (24 bars assuming hourly) and 7d (168 bars)
    to compute pct_change_24h / pct_change_7d, then runs the same decision tree.
    """
    out: list[Forecast] = []
    for sym, bars in window.items():
        if len(bars) < 168:
            continue
        last = bars[-1].close
        c_24 = bars[-24].close
        c_7d = bars[-168].close
        pct_24 = _pct(c_24, last)
        pct_7d = _pct(c_7d, last)

        if pct_24 > 0.5 and pct_7d > 2.0:
            conf = min(1.0, 0.5 + abs(pct_7d) / 20)
            out.append(Forecast(sym, "long", round(conf, 3)))
        elif pct_24 < -0.5 and pct_7d < -2.0:
            conf = min(1.0, 0.5 + abs(pct_7d) / 20)
            out.append(Forecast(sym, "short", round(conf, 3)))
        elif pct_7d < -10 and pct_24 > 0:
            out.append(Forecast(sym, "long", 0.55))
        else:
            out.append(Forecast(sym, "flat", 0.4))
    return out
