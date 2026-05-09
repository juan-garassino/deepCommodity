#!/usr/bin/env python
"""V1+ forecaster router.

Backends (selected via --model):
  rule-based     : the bundled hand-coded signal (Phases 0–4 default)
  price          : Phase 5 price transformer       (data/models/<SYM>.pt)
  orderflow      : Phase 6 order-flow transformer  (data/models/<SYM>.orderflow.pt)
  news           : Phase 7 sentiment scorer        (no checkpoint needed for rule-based)
  fused          : Phase 8 fused multi-modal       (data/models/<SYM>.fused.pt)
  ensemble       : weighted average of available models for the symbol

Output (always):
  {"forecasts": [{"symbol": ..., "direction": "long|short|flat",
                   "confidence": 0..1, "rationale": "..."}, ...]}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA_MODELS = ROOT / "data" / "models"


# ---- rule-based (no torch) -------------------------------------------------

def _signal(pct_24h, pct_7d):
    if pct_7d is None or pct_24h is None:
        return "flat", 0.0, "missing data"
    if pct_24h > 0.5 and pct_7d > 2.0:
        conf = min(1.0, 0.5 + abs(pct_7d) / 20)
        return "long", round(conf, 3), f"momentum 24h={pct_24h:.2f}% 7d={pct_7d:.2f}%"
    if pct_24h < -0.5 and pct_7d < -2.0:
        conf = min(1.0, 0.5 + abs(pct_7d) / 20)
        return "short", round(conf, 3), f"breakdown 24h={pct_24h:.2f}% 7d={pct_7d:.2f}%"
    if pct_7d < -10 and pct_24h > 0:
        return "long", 0.55, f"mean-reversion bounce after 7d={pct_7d:.2f}%"
    return "flat", 0.4, f"mixed 24h={pct_24h:.2f}% 7d={pct_7d:.2f}%"


def rule_based(symbols_data: dict[str, dict]) -> list[dict]:
    out = []
    for sym, d in symbols_data.items():
        direction, conf, rat = _signal(d.get("pct_change_24h"), d.get("pct_change_7d"))
        out.append({"symbol": sym, "direction": direction, "confidence": conf,
                    "rationale": f"[rule-based] {rat}"})
    return out


# ---- transformer specialists (torch lazy) ---------------------------------

def _load_price_model(symbol: str):
    path = DATA_MODELS / f"{symbol.upper()}.pt"
    if not path.exists():
        return None
    import torch
    from deepCommodity.model.price_transformer import TransformerConfig, build_model
    ckpt = torch.load(path, map_location="cpu")
    cfg = TransformerConfig(**ckpt["config"])
    model = build_model(cfg)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model, cfg


def _load_orderflow_model(symbol: str):
    path = DATA_MODELS / f"{symbol.upper()}.orderflow.pt"
    if not path.exists():
        return None
    import torch
    from deepCommodity.model.orderflow_transformer import OrderflowConfig, build_model
    ckpt = torch.load(path, map_location="cpu")
    cfg = OrderflowConfig(**ckpt["config"])
    model = build_model(cfg)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model, cfg


def _price_predict(symbol: str, bars_csv: Path) -> dict | None:
    if not bars_csv.exists():
        return None
    loaded = _load_price_model(symbol)
    if loaded is None:
        return None
    model, cfg = loaded
    import pandas as pd
    from deepCommodity.model.price_transformer import (
        make_features, predict_proba, proba_to_forecast,
    )
    df = pd.read_csv(bars_csv)
    feats = make_features(df)
    if len(feats) < cfg.seq_len:
        return None
    X = feats[-cfg.seq_len:][None, :, :]
    proba = predict_proba(model, X)[0]
    direction, conf = proba_to_forecast(proba, min_conf=0.0)
    return {"symbol": symbol, "direction": direction, "confidence": round(conf, 3),
            "rationale": f"[price] proba=[{proba[0]:.2f}/{proba[1]:.2f}/{proba[2]:.2f}]"}


def _orderflow_predict(symbol: str, of_csv: Path) -> dict | None:
    if not of_csv.exists():
        return None
    loaded = _load_orderflow_model(symbol)
    if loaded is None:
        return None
    model, cfg = loaded
    import pandas as pd
    from deepCommodity.model.orderflow_transformer import (
        make_features, predict_proba, proba_to_forecast,
    )
    df = pd.read_csv(of_csv)
    feats = make_features(df)
    if len(feats) < cfg.seq_len:
        return None
    X = feats[-cfg.seq_len:][None, :, :]
    proba = predict_proba(model, X)[0]
    direction, conf = proba_to_forecast(proba, min_conf=0.0)
    return {"symbol": symbol, "direction": direction, "confidence": round(conf, 3),
            "rationale": f"[orderflow] proba=[{proba[0]:.2f}/{proba[1]:.2f}/{proba[2]:.2f}]"}


# ---- news -----------------------------------------------------------------

def _news_predict(symbol: str, news_text: str) -> dict:
    from deepCommodity.model.news_model import get_sentiment_backend
    backend = get_sentiment_backend()
    s = backend.score(news_text or "")
    if s.value > 0.2 and s.confidence > 0.3:
        d = "long"
    elif s.value < -0.2 and s.confidence > 0.3:
        d = "short"
    else:
        d = "flat"
    return {"symbol": symbol, "direction": d, "confidence": round(float(s.confidence), 3),
            "rationale": f"[news/{backend.name}] sent={s.value:+.2f}"}


# ---- ensemble -------------------------------------------------------------

def _ensemble(predictions: list[dict]) -> dict | None:
    if not predictions:
        return None
    sym = predictions[0]["symbol"]
    score = 0.0
    weight = 0.0
    rationales = []
    for p in predictions:
        s = {"long": +1, "short": -1, "flat": 0}[p["direction"]]
        c = p["confidence"]
        score += s * c
        weight += c
        rationales.append(p["rationale"])
    avg_conf = weight / len(predictions) if predictions else 0.0
    if score > 0.15 and avg_conf > 0.3:
        d = "long"
    elif score < -0.15 and avg_conf > 0.3:
        d = "short"
    else:
        d = "flat"
    return {"symbol": sym, "direction": d, "confidence": round(min(1.0, abs(score)), 3),
            "rationale": "[ensemble] " + " | ".join(rationales)}


# ---- I/O ------------------------------------------------------------------

def _load_inputs(paths: list[str]) -> dict[str, dict]:
    merged = {}
    for src in paths:
        text = sys.stdin.read() if src == "-" else Path(src).read_text()
        merged.update(json.loads(text).get("symbols", {}))
    return merged


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", action="append", default=[],
                   help="fetch_*.py JSON (repeatable; - for stdin) — used by rule-based & symbol list")
    p.add_argument("--symbols", default="",
                   help="optional override of symbols to forecast (else from --input)")
    p.add_argument("--model", default="rule-based",
                   choices=["rule-based", "price", "orderflow", "news", "fused", "ensemble"])
    p.add_argument("--bars-dir", default=str(ROOT / "data" / "bars"))
    p.add_argument("--orderflow-dir", default=str(ROOT / "data" / "orderflow"))
    p.add_argument("--news-input", help="path to fetch_news.py JSON for the news/ensemble path")
    args = p.parse_args()

    symbols_data = _load_inputs(args.input) if args.input else {}
    if args.symbols:
        wanted = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        wanted = list(symbols_data.keys()) or []
    if not wanted:
        sys.exit("no symbols (provide --symbols or --input with symbol map)")

    news_text = ""
    if args.news_input:
        news_text = json.loads(Path(args.news_input).read_text()).get("digest", "")

    forecasts: list[dict] = []
    bars_dir = Path(args.bars_dir)
    of_dir = Path(args.orderflow_dir)

    for sym in wanted:
        if args.model == "rule-based":
            d = symbols_data.get(sym, {})
            direction, conf, rat = _signal(d.get("pct_change_24h"), d.get("pct_change_7d"))
            forecasts.append({"symbol": sym, "direction": direction,
                              "confidence": conf, "rationale": f"[rule-based] {rat}"})
            continue
        if args.model == "price":
            f = _price_predict(sym, bars_dir / f"{sym}.csv")
            if f: forecasts.append(f)
            continue
        if args.model == "orderflow":
            f = _orderflow_predict(sym, of_dir / f"{sym}.csv")
            if f: forecasts.append(f)
            continue
        if args.model == "news":
            forecasts.append(_news_predict(sym, news_text))
            continue
        if args.model in ("fused", "ensemble"):
            preds = []
            d = symbols_data.get(sym, {})
            direction, conf, rat = _signal(d.get("pct_change_24h"), d.get("pct_change_7d"))
            preds.append({"symbol": sym, "direction": direction, "confidence": conf,
                          "rationale": f"[rule-based] {rat}"})
            f = _price_predict(sym, bars_dir / f"{sym}.csv")
            if f: preds.append(f)
            f = _orderflow_predict(sym, of_dir / f"{sym}.csv")
            if f: preds.append(f)
            if news_text:
                preds.append(_news_predict(sym, news_text))
            agg = _ensemble(preds)
            if agg: forecasts.append(agg)

    print(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": args.model,
        "forecasts": forecasts,
    }, indent=2))


if __name__ == "__main__":
    main()
