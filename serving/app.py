"""deepCommodity inference API.

Endpoints
    GET  /health                     liveness + available models
    POST /forecast                   run a forecast (auth required)
    POST /reload                     reload models from disk (auth required)

Run locally:
    uvicorn serving.app:app --host 0.0.0.0 --port 8080

Or via Docker:
    docker compose -f serving/docker-compose.yml up -d
"""
from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, status

# Repo root on path so we can import deepCommodity.*
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serving.auth import require_api_key  # noqa: E402
from serving.registry import ModelRegistry, get_models_dir  # noqa: E402
from serving.schemas import (  # noqa: E402
    ForecastRequest,
    ForecastResponse,
    HealthResponse,
    ReloadResponse,
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s | %(message)s")
log = logging.getLogger("dc-serve")

REGISTRY: ModelRegistry | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global REGISTRY
    REGISTRY = ModelRegistry(get_models_dir())
    REGISTRY.load_all()
    if not os.getenv("DC_API_KEY"):
        log.warning("DC_API_KEY not set — API is in OPEN mode. Do not deploy publicly.")
    yield


app = FastAPI(title="deepCommodity inference",
              version="1.0.0",
              lifespan=lifespan)


# ---- helpers ---------------------------------------------------------------

def _torch_available() -> bool:
    try:
        import torch  # noqa: F401
        return True
    except ImportError:
        return False


def _bars_to_df(b) -> pd.DataFrame:
    n = min(len(b.open), len(b.high), len(b.low), len(b.close), len(b.volume))
    return pd.DataFrame({
        "open":   b.open[-n:],
        "high":   b.high[-n:],
        "low":    b.low[-n:],
        "close":  b.close[-n:],
        "volume": b.volume[-n:],
    })


def _orderflow_to_df(o) -> pd.DataFrame:
    return pd.DataFrame({
        "signed_volume": o.signed_volume,
        "trade_count":   o.trade_count,
        "mean_size":     o.mean_size,
        "vwap_drift":    o.vwap_drift,
    })


# ---- prediction adapters --------------------------------------------------

def _predict_price(symbol: str, bars_df: pd.DataFrame) -> tuple[str, float, list[float]]:
    if REGISTRY is None:
        raise HTTPException(503, "registry not initialized")
    loaded = REGISTRY.get(symbol, "price")
    if loaded is None:
        raise HTTPException(404, f"no price model for {symbol}")
    from deepCommodity.model.price_transformer import (
        make_features, predict_proba, proba_to_forecast,
    )
    seq_len = loaded.config["seq_len"]
    feats = make_features(bars_df)
    if len(feats) < seq_len:
        raise HTTPException(422, f"need {seq_len} bars, got {len(feats)}")
    X = feats[-seq_len:][None, :, :].astype(np.float32)
    proba = predict_proba(loaded.handle, X)[0]
    direction, conf = proba_to_forecast(proba)
    return direction, conf, proba.tolist()


def _predict_orderflow(symbol: str, of_df: pd.DataFrame) -> tuple[str, float, list[float]]:
    if REGISTRY is None:
        raise HTTPException(503, "registry not initialized")
    loaded = REGISTRY.get(symbol, "orderflow")
    if loaded is None:
        raise HTTPException(404, f"no orderflow model for {symbol}")
    from deepCommodity.model.orderflow_transformer import (
        make_features, predict_proba, proba_to_forecast,
    )
    seq_len = loaded.config["seq_len"]
    feats = make_features(of_df)
    if len(feats) < seq_len:
        raise HTTPException(422, f"need {seq_len} flow bars, got {len(feats)}")
    X = feats[-seq_len:][None, :, :].astype(np.float32)
    proba = predict_proba(loaded.handle, X)[0]
    direction, conf = proba_to_forecast(proba)
    return direction, conf, proba.tolist()


def _predict_news(text: str) -> tuple[str, float, list[float] | None]:
    from deepCommodity.model.news_model import get_sentiment_backend
    backend = get_sentiment_backend()
    s = backend.score(text or "")
    if s.value > 0.2 and s.confidence > 0.3:
        direction = "long"
    elif s.value < -0.2 and s.confidence > 0.3:
        direction = "short"
    else:
        direction = "flat"
    return direction, float(s.confidence), None


def _predict_rule_based(pct_24h: float | None, pct_7d: float | None) -> tuple[str, float, list[float] | None]:
    if pct_24h is None or pct_7d is None:
        return "flat", 0.0, None
    if pct_24h > 0.5 and pct_7d > 2.0:
        conf = min(1.0, 0.5 + abs(pct_7d) / 20)
        return "long", round(conf, 3), None
    if pct_24h < -0.5 and pct_7d < -2.0:
        conf = min(1.0, 0.5 + abs(pct_7d) / 20)
        return "short", round(conf, 3), None
    if pct_7d < -10 and pct_24h > 0:
        return "long", 0.55, None
    return "flat", 0.4, None


def _ensemble(predictions: list[tuple[str, str, float]]) -> tuple[str, float, str]:
    """Weighted vote over [(backend, direction, confidence), ...]."""
    if not predictions:
        return "flat", 0.0, "no backends produced output"
    score = 0.0
    weight = 0.0
    parts = []
    for backend, direction, conf in predictions:
        s = {"long": +1, "short": -1, "flat": 0}[direction]
        score += s * conf
        weight += conf
        parts.append(f"{backend}={direction}@{conf:.2f}")
    avg_conf = weight / len(predictions)
    if score > 0.15 and avg_conf > 0.3:
        d = "long"
    elif score < -0.15 and avg_conf > 0.3:
        d = "short"
    else:
        d = "flat"
    return d, round(min(1.0, abs(score)), 3), " | ".join(parts)


# ---- endpoints ------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    available = REGISTRY.list_available() if REGISTRY else {}
    return HealthResponse(
        ok=True,
        available_models=available,
        torch_available=_torch_available(),
    )


@app.post("/reload", response_model=ReloadResponse,
          dependencies=[Depends(require_api_key)])
def reload_models() -> ReloadResponse:
    if REGISTRY is None:
        raise HTTPException(503, "registry not initialized")
    t0 = time.time()
    loaded = REGISTRY.load_all()
    return ReloadResponse(reloaded=loaded, elapsed_ms=int((time.time() - t0) * 1000))


@app.post("/forecast", response_model=ForecastResponse,
          dependencies=[Depends(require_api_key)])
def forecast(req: ForecastRequest) -> ForecastResponse:
    sym = req.symbol.upper()
    backends_used: list[str] = []

    if req.model == "price":
        if not req.bars:
            raise HTTPException(422, "model=price requires bars")
        direction, conf, proba = _predict_price(sym, _bars_to_df(req.bars))
        return ForecastResponse(
            symbol=sym, model="price", direction=direction,
            confidence=conf, proba=proba,
            rationale=f"price proba=[{proba[0]:.2f}/{proba[1]:.2f}/{proba[2]:.2f}]",
            backends_used=["price"],
        )

    if req.model == "orderflow":
        if not req.orderflow:
            raise HTTPException(422, "model=orderflow requires orderflow window")
        direction, conf, proba = _predict_orderflow(sym, _orderflow_to_df(req.orderflow))
        return ForecastResponse(
            symbol=sym, model="orderflow", direction=direction,
            confidence=conf, proba=proba,
            rationale=f"orderflow proba=[{proba[0]:.2f}/{proba[1]:.2f}/{proba[2]:.2f}]",
            backends_used=["orderflow"],
        )

    if req.model == "news":
        direction, conf, proba = _predict_news(req.news_text or "")
        return ForecastResponse(
            symbol=sym, model="news", direction=direction,
            confidence=conf, proba=proba,
            rationale=f"news sentiment direction={direction}",
            backends_used=["news"],
        )

    if req.model == "rule-based":
        direction, conf, proba = _predict_rule_based(req.pct_change_24h, req.pct_change_7d)
        return ForecastResponse(
            symbol=sym, model="rule-based", direction=direction,
            confidence=conf, proba=proba,
            rationale=f"rule-based: 24h={req.pct_change_24h} 7d={req.pct_change_7d}",
            backends_used=["rule-based"],
        )

    if req.model in ("ensemble", "fused"):
        results = []
        rationales = []
        if req.bars and REGISTRY and REGISTRY.get(sym, "price"):
            try:
                d, c, p = _predict_price(sym, _bars_to_df(req.bars))
                results.append(("price", d, c)); rationales.append(f"price={d}@{c:.2f}")
                backends_used.append("price")
            except HTTPException:
                pass
        if req.orderflow and REGISTRY and REGISTRY.get(sym, "orderflow"):
            try:
                d, c, p = _predict_orderflow(sym, _orderflow_to_df(req.orderflow))
                results.append(("orderflow", d, c)); rationales.append(f"orderflow={d}@{c:.2f}")
                backends_used.append("orderflow")
            except HTTPException:
                pass
        if req.news_text:
            d, c, _ = _predict_news(req.news_text)
            results.append(("news", d, c)); rationales.append(f"news={d}@{c:.2f}")
            backends_used.append("news")
        if req.pct_change_24h is not None and req.pct_change_7d is not None:
            d, c, _ = _predict_rule_based(req.pct_change_24h, req.pct_change_7d)
            results.append(("rule-based", d, c)); rationales.append(f"rule-based={d}@{c:.2f}")
            backends_used.append("rule-based")
        if not results:
            raise HTTPException(422,
                "ensemble needs at least one of: bars (with trained model), "
                "orderflow (with trained model), news_text, or pct_change_*")
        direction, conf, _ = _ensemble(results)
        return ForecastResponse(
            symbol=sym, model=req.model, direction=direction,
            confidence=conf, proba=None,
            rationale="ensemble: " + " | ".join(rationales),
            backends_used=backends_used,
        )

    raise HTTPException(400, f"unsupported model {req.model}")
