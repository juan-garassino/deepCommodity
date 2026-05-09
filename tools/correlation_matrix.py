#!/usr/bin/env python
"""Cross-asset correlation matrix + regime-break detector.

Pulls 90d daily closes for a fixed universe of macro proxies, computes:
  1. Pairwise Pearson correlation over the full window (baseline).
  2. Pairwise correlation over the last 5 trading days (recent).
  3. Flags pairs where |recent - baseline| >= 0.30 — these are 'regime breaks'.

Why it matters:
- Normally BTC-DXY correlation is around -0.3 to -0.5 (dollar up = BTC down).
- If today's 5d shows BTC-DXY at +0.4, something fundamental shifted.
- Same logic for SPY-VIX, equity-bond, gold-real-rates, etc.
- Regime breaks are the EARLIEST signal of a change in market psychology.

Universe (macro proxies):
  SPY, QQQ, IWM       — equity (large/mega/small)
  BTC, ETH            — crypto
  GLD                 — gold
  UUP                 — US dollar (DXY proxy ETF; DXY direct not on yfinance)
  ^VIX                — vol
  ^TNX                — 10y treasury yield
  HYG                 — high-yield corp bonds (credit risk)
  USO                 — crude oil
  KRE                 — regional banks (financial stress proxy)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEFAULT_UNIVERSE = ["SPY", "QQQ", "IWM", "GLD", "UUP",
                    "^VIX", "^TNX", "HYG", "USO", "KRE"]
DEFAULT_CRYPTO = ["BTC", "ETH"]


def fetch_yf_returns(symbols: list[str], days: int = 90) -> dict[str, list[float]]:
    """Daily log-returns for each ticker. Empty list on any failure."""
    try:
        import yfinance as yf  # type: ignore
        import pandas as pd  # noqa: F401
    except ImportError:
        return {}

    try:
        data = yf.download(symbols, period=f"{days}d", interval="1d",
                           progress=False, auto_adjust=True)
        if data.empty:
            return {}
        closes = data["Close"] if isinstance(data.columns, type(data.columns))\
                                  and "Close" in data.columns.get_level_values(0)\
                               else data
        out: dict[str, list[float]] = {}
        for sym in symbols:
            try:
                series = closes[sym].dropna() if sym in closes.columns else None
            except Exception:
                series = None
            if series is None or len(series) < 5:
                continue
            rets = series.pct_change().dropna().tolist()
            out[sym] = rets
        return out
    except Exception:  # noqa: BLE001
        return {}


def fetch_crypto_returns(symbols: list[str], days: int = 90) -> dict[str, list[float]]:
    """Daily returns for crypto via Binance public klines."""
    import requests
    out: dict[str, list[float]] = {}
    for sym in symbols:
        pair = f"{sym}USDT"
        try:
            r = requests.get("https://api.binance.com/api/v3/klines",
                             params={"symbol": pair, "interval": "1d", "limit": days},
                             timeout=15)
            r.raise_for_status()
            klines = r.json()
            closes = [float(k[4]) for k in klines]
            rets = [math.log(closes[i] / closes[i - 1])
                    for i in range(1, len(closes))]
            out[sym] = rets
        except Exception:  # noqa: BLE001
            continue
    return out


def pearson(a: list[float], b: list[float]) -> float | None:
    n = min(len(a), len(b))
    if n < 5:
        return None
    a = a[-n:]; b = b[-n:]
    ma = sum(a) / n; mb = sum(b) / n
    sxy = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    sxx = sum((x - ma) ** 2 for x in a)
    syy = sum((y - mb) ** 2 for y in b)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def matrix(returns: dict[str, list[float]]) -> dict[tuple[str, str], float]:
    syms = sorted(returns)
    out: dict[tuple[str, str], float] = {}
    for i, a in enumerate(syms):
        for b in syms[i + 1:]:
            c = pearson(returns[a], returns[b])
            if c is not None:
                out[(a, b)] = round(c, 3)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=90, help="baseline window")
    p.add_argument("--recent", type=int, default=5, help="recent window (days)")
    p.add_argument("--break-threshold", type=float, default=0.30,
                   help="|recent - baseline| flag threshold")
    args = p.parse_args()

    eq_rets = fetch_yf_returns(DEFAULT_UNIVERSE, args.days)
    crypto_rets = fetch_crypto_returns(DEFAULT_CRYPTO, args.days)
    rets = {**eq_rets, **crypto_rets}

    if len(rets) < 3:
        print(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "error": "insufficient data",
            "have": list(rets.keys()),
        }, indent=2))
        sys.exit(0)

    # truncate to the same last-N days for fair comparison
    min_len = min(len(v) for v in rets.values())
    rets = {k: v[-min_len:] for k, v in rets.items()}

    full = matrix(rets)
    recent_rets = {k: v[-args.recent:] for k, v in rets.items() if len(v) >= args.recent}
    recent = matrix(recent_rets)

    breaks = []
    for pair, base in full.items():
        r = recent.get(pair)
        if r is None:
            continue
        diff = abs(r - base)
        if diff >= args.break_threshold:
            breaks.append({
                "pair": f"{pair[0]}/{pair[1]}",
                "baseline_corr": base,
                "recent_corr": r,
                "delta": round(r - base, 3),
                "abs_delta": round(diff, 3),
            })
    breaks.sort(key=lambda x: x["abs_delta"], reverse=True)

    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "universe": list(rets.keys()),
        "baseline_window_days": args.days,
        "recent_window_days": args.recent,
        "n_pairs": len(full),
        "regime_breaks": breaks[:10],
        "baseline_matrix_top5_negative": sorted(
            [{"pair": f"{k[0]}/{k[1]}", "corr": v} for k, v in full.items()],
            key=lambda x: x["corr"])[:5],
        "baseline_matrix_top5_positive": sorted(
            [{"pair": f"{k[0]}/{k[1]}", "corr": v} for k, v in full.items()],
            key=lambda x: x["corr"], reverse=True)[:5],
    }, indent=2))


if __name__ == "__main__":
    main()
