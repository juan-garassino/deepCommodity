#!/usr/bin/env python
"""Run a backtest against a CSV/JSON of historical bars.

CSV format: one file per symbol, columns: ts (ISO), close, [volume]
  --bars-dir data/bars/  -> reads data/bars/BTC.csv, data/bars/ETH.csv, ...

JSON format: {"BTC": [{"ts": ..., "close": ...}, ...], "ETH": [...], ...}
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.backtest import BacktestConfig, run_backtest  # noqa: E402
from deepCommodity.backtest.engine import Bar  # noqa: E402
from deepCommodity.backtest.forecasters import rule_based  # noqa: E402


def _parse_ts(s: str) -> datetime:
    # tolerate trailing Z, Unix ms, and ISO with offset
    if s.isdigit():
        v = int(s)
        if v > 10**12:  # ms
            return datetime.fromtimestamp(v / 1000)
        return datetime.fromtimestamp(v)
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


def _load_csv_dir(path: Path) -> dict[str, list[Bar]]:
    out: dict[str, list[Bar]] = {}
    for f in sorted(path.glob("*.csv")):
        sym = f.stem.upper()
        bars: list[Bar] = []
        with f.open() as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                ts = _parse_ts(row.get("ts") or row.get("timestamp") or row.get("date") or "")
                close = float(row["close"])
                vol = float(row.get("volume") or 0.0)
                bars.append(Bar(ts=ts, close=close, volume=vol))
        bars.sort(key=lambda b: b.ts)
        out[sym] = bars
    return out


def _load_json(path: Path) -> dict[str, list[Bar]]:
    raw = json.loads(path.read_text())
    out: dict[str, list[Bar]] = {}
    for sym, rows in raw.items():
        bars = [Bar(ts=_parse_ts(r["ts"]), close=float(r["close"]),
                    volume=float(r.get("volume", 0))) for r in rows]
        bars.sort(key=lambda b: b.ts)
        out[sym] = bars
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--bars-dir", help="directory of <SYMBOL>.csv files")
    src.add_argument("--bars-json", help="single JSON file {symbol: [{ts,close,volume},...]}")
    p.add_argument("--starting-nav", type=float, default=10_000.0)
    p.add_argument("--position-pct", type=float, default=0.05)
    p.add_argument("--min-confidence", type=float, default=0.60)
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--slippage-bps", type=float, default=2.0)
    p.add_argument("--warmup", type=int, default=168)
    p.add_argument("--rebalance-every", type=int, default=1)
    p.add_argument("--trades-out", help="optional path to write trade ledger CSV")
    args = p.parse_args()

    bars = _load_csv_dir(Path(args.bars_dir)) if args.bars_dir else _load_json(Path(args.bars_json))
    if not bars:
        sys.exit("no bars loaded")

    cfg = BacktestConfig(
        starting_nav=args.starting_nav,
        position_pct=args.position_pct,
        min_confidence=args.min_confidence,
        transaction_cost_bps=args.cost_bps,
        slippage_bps=args.slippage_bps,
        warmup_bars=args.warmup,
        rebalance_every=args.rebalance_every,
    )
    res = run_backtest(bars, rule_based, cfg)

    print(json.dumps({
        "starting_nav": cfg.starting_nav,
        "final_nav": round(res.final_nav, 2),
        "return_pct": round(res.return_pct * 100, 3),
        "sharpe": round(res.sharpe, 3),
        "max_drawdown_pct": round(res.max_drawdown * 100, 3),
        "n_trades": res.n_trades,
        "n_blocked": res.n_blocked,
        "win_rate": round(res.win_rate, 3),
    }, indent=2))

    if args.trades_out:
        with open(args.trades_out, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ts", "symbol", "side", "qty", "price", "notional", "cost"])
            for t in res.trades:
                w.writerow([t.ts.isoformat(), t.symbol, t.side, t.qty,
                            t.price, t.notional, t.cost])


if __name__ == "__main__":
    main()
