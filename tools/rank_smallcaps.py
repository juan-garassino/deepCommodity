#!/usr/bin/env python
"""Score opportunities by momentum, log-inverse market cap, and volume.

Input: JSON file (or stdin) with shape produced by fetch_crypto.py / fetch_equities.py:
  {"symbols": {"BTC": {"price_usd":..., "market_cap_usd":..., "pct_change_7d":...,
                       "total_volume_usd":..., ...}, ...}}

Multiple files may be passed; their symbol maps are merged.

Output: JSON {"ranked": [{"symbol":..., "score":..., "components": {...}}, ...]}
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_WEIGHTS = {"momentum": 0.4, "mcap": 0.4, "volume": 0.2}


def _zscore(values: list[float]) -> list[float]:
    if not values:
        return []
    mu = sum(values) / len(values)
    var = sum((v - mu) ** 2 for v in values) / len(values)
    sd = math.sqrt(var) if var > 0 else 1.0
    return [(v - mu) / sd for v in values]


def _norm01(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi - lo < 1e-12:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def rank(symbols: dict[str, dict], weights: dict[str, float]) -> list[dict]:
    items = [(s, d) for s, d in symbols.items()
             if d.get("market_cap_usd") and d.get("price_usd")]
    if not items:
        return []
    momenta = [(d.get("pct_change_7d") or 0.0) for _, d in items]
    inv_mcap = [-math.log10(max(d["market_cap_usd"], 1.0)) for _, d in items]
    vols = [(d.get("total_volume_usd") or d.get("volume") or 0.0) for _, d in items]

    m_n = _norm01(_zscore(momenta))
    c_n = _norm01(inv_mcap)
    v_n = _norm01(_zscore(vols))

    out = []
    for (sym, d), m, c, v in zip(items, m_n, c_n, v_n):
        score = weights["momentum"] * m + weights["mcap"] * c + weights["volume"] * v
        out.append({"symbol": sym, "score": round(score, 4),
                    "components": {"momentum": round(m, 4), "mcap": round(c, 4),
                                   "volume": round(v, 4)},
                    "price_usd": d.get("price_usd"),
                    "market_cap_usd": d.get("market_cap_usd")})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def _load(path: str) -> dict:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, action="append",
                   help="path to fetch_*.py JSON output (use - for stdin). Repeatable.")
    p.add_argument("--w-momentum", type=float, default=DEFAULT_WEIGHTS["momentum"])
    p.add_argument("--w-mcap", type=float, default=DEFAULT_WEIGHTS["mcap"])
    p.add_argument("--w-volume", type=float, default=DEFAULT_WEIGHTS["volume"])
    p.add_argument("--top", type=int, default=10)
    args = p.parse_args()

    merged: dict[str, dict] = {}
    for src in args.input:
        merged.update(_load(src).get("symbols", {}))

    weights = {"momentum": args.w_momentum, "mcap": args.w_mcap, "volume": args.w_volume}
    total = sum(weights.values()) or 1.0
    weights = {k: v / total for k, v in weights.items()}

    ranked = rank(merged, weights)[: args.top]
    print(json.dumps({"weights": weights, "ranked": ranked}, indent=2))


if __name__ == "__main__":
    main()
