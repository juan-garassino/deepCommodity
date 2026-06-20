#!/usr/bin/env python
"""Backtest all named risk portfolios over the crypto universe and compare them.

Loads daily bars + funding + macro regime, builds the XS / CARRY / DIR sleeves,
blends them per portfolio (deepCommodity/portfolio/portfolios.yaml), runs the
honest portfolio backtester (costs + funding + vol-target + DD ladder), and writes
a side-by-side risk-adjusted comparison. This is the decision gate before any live
shorting/leverage wiring.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.portfolio import load_funding, load_prices, load_regime  # noqa: E402
from deepCommodity.portfolio import backtest, sleeves, signals  # noqa: E402
from deepCommodity.portfolio.portfolios import build_weights, load_portfolios  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", help="override universe (comma-separated)")
    p.add_argument("--bars-dir", default=str(ROOT / "data" / "bars"))
    p.add_argument("--funding-dir", default=str(ROOT / "data" / "funding"))
    p.add_argument("--macro", default=str(ROOT / "data" / "macro" / "features.csv"))
    p.add_argument("--report-dir", default=str(ROOT / "data" / "reports"))
    args = p.parse_args()

    if args.symbols:
        syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        from deepCommodity.universe import Universe
        syms = Universe.load().all_crypto_symbols()

    prices = load_prices(syms, Path(args.bars_dir))
    rets = prices.pct_change()
    funding = load_funding(prices.columns, Path(args.funding_dir), prices.index)
    regime = load_regime(Path(args.macro), prices.index)

    xs_w = sleeves.xs_weights(signals.xs_score(prices))
    carry_w = sleeves.carry_weights(signals.carry_score(funding))
    dir_w = sleeves.dir_weights(regime, prices.columns)

    book = load_portfolios()
    results = []
    for name, cfg in book.cfgs.items():
        pw, cw = build_weights(cfg, xs_w, carry_w, dir_w)
        results.append(backtest.run(pw, cw, rets, funding, cfg, book.costs))

    report = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "universe": list(prices.columns), "n_assets": prices.shape[1],
              "span": [str(prices.index.min().date()), str(prices.index.max().date())],
              "portfolios": results}

    rep_dir = Path(args.report_dir); rep_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    (rep_dir / f"portfolio_backtest_{stamp}.md").write_text(
        f"# Risk-portfolio backtest ({stamp})\n\n"
        f"{prices.shape[1]} assets, {report['span'][0]}→{report['span'][1]}\n\n"
        f"```json\n{json.dumps(report, indent=2)}\n```\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
