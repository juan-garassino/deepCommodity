"""Request / response schemas for the inference API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ModelKind = Literal["price", "orderflow", "news", "fused", "ensemble", "rule-based"]


class OHLCVWindow(BaseModel):
    open: list[float] = Field(..., min_length=2)
    high: list[float] = Field(..., min_length=2)
    low: list[float] = Field(..., min_length=2)
    close: list[float] = Field(..., min_length=2)
    volume: list[float] = Field(..., min_length=2)


class OrderflowWindow(BaseModel):
    signed_volume: list[float] = Field(..., min_length=2)
    trade_count: list[float] = Field(..., min_length=2)
    mean_size: list[float] = Field(..., min_length=2)
    vwap_drift: list[float] = Field(..., min_length=2)


class ForecastRequest(BaseModel):
    symbol: str
    model: ModelKind = "price"
    bars: OHLCVWindow | None = None         # required for price / fused / ensemble
    orderflow: OrderflowWindow | None = None  # required for orderflow / fused / ensemble
    news_text: str | None = None              # required for news / fused / ensemble
    pct_change_24h: float | None = None       # for rule-based fallback inside ensemble
    pct_change_7d: float | None = None


class ForecastResponse(BaseModel):
    symbol: str
    model: ModelKind
    direction: Literal["long", "short", "flat"]
    confidence: float
    proba: list[float] | None = None
    rationale: str
    model_version: str | None = None
    backends_used: list[str] = []


class HealthResponse(BaseModel):
    ok: bool
    available_models: dict[str, list[str]]   # {"price": ["BTC", "ETH"], "orderflow": [...]}
    torch_available: bool
    version: str = "1.0.0"


class ReloadResponse(BaseModel):
    reloaded: dict[str, list[str]]
    elapsed_ms: int
