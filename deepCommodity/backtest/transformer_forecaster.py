"""Adapter: trained price-transformer -> backtest forecaster callable.

Holds one transformer per symbol. On each window, slices the last `seq_len`
bars per symbol, builds features, runs predict_proba, and emits a Forecast.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from deepCommodity.backtest.engine import Bar, Forecast


@dataclass
class TransformerForecaster:
    models: dict[str, Any]               # symbol -> torch.nn.Module
    seq_len: int = 168
    min_confidence: float = 0.55

    def __call__(self, window: dict[str, list[Bar]]) -> list[Forecast]:
        from deepCommodity.model.price_transformer import (
            make_features,
            predict_proba,
            proba_to_forecast,
        )
        out: list[Forecast] = []
        for sym, bars in window.items():
            mdl = self.models.get(sym)
            if mdl is None or len(bars) < self.seq_len + 1:
                continue
            recent = bars[-(self.seq_len + 1):]   # +1 for pct_change drop
            df = pd.DataFrame({
                "open":  [b.close for b in recent],   # OHLCV not on Bar; fallback to close
                "high":  [b.close for b in recent],
                "low":   [b.close for b in recent],
                "close": [b.close for b in recent],
                "volume":[b.volume for b in recent],
            })
            feats = make_features(df)
            if len(feats) < self.seq_len:
                continue
            X = feats[-self.seq_len:][None, :, :]
            proba = predict_proba(mdl, X)[0]
            direction, conf = proba_to_forecast(proba, self.min_confidence)
            out.append(Forecast(symbol=sym, direction=direction, confidence=conf))
        return out
