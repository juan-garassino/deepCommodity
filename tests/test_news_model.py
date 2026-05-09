"""Phase 7 news/sentiment model.

Rule-based backend has no deps; sklearn backend is opt-skip if scikit-learn missing;
HuggingFace backend is opt-skip (network-bound, slow).
"""
from __future__ import annotations

import os

import pytest

from deepCommodity.model.news_model import (
    RuleBasedSentiment,
    SentimentScore,
    get_sentiment_backend,
)


def test_rulebased_bullish():
    s = RuleBasedSentiment().score(
        "BTC ETF inflows surge to ATH; analysts upgrade target as institutional buy resumes."
    )
    assert s.value > 0.0
    assert s.confidence > 0.0


def test_rulebased_bearish():
    s = RuleBasedSentiment().score(
        "Major exchange hack triggers crash and bankruptcy fears; outflows hit a record."
    )
    assert s.value < 0.0
    assert s.confidence > 0.0


def test_rulebased_neutral_when_empty():
    s = RuleBasedSentiment().score("")
    assert s == SentimentScore(0.0, 0.0)


def test_rulebased_neutral_when_balanced():
    s = RuleBasedSentiment().score(
        "Mixed picture: rally meets crash, upgrade meets downgrade, inflows meet outflows."
    )
    assert abs(s.value) < 0.5


def test_factory_returns_rulebased_by_default(monkeypatch):
    monkeypatch.delenv("SENTIMENT_BACKEND", raising=False)
    assert get_sentiment_backend().name == "rule-based"


def test_factory_unknown_backend_raises():
    with pytest.raises(ValueError):
        get_sentiment_backend("not-a-backend")


def test_sklearn_backend_trains_and_scores():
    sk = pytest.importorskip("sklearn")
    from deepCommodity.model.news_model import SklearnSentiment
    texts = [
        "rally surge bull buy upgrade", "rally surge bull buy ath",
        "crash plunge bear sell downgrade", "crash plunge bear hack lawsuit",
        "neutral news no movement today", "flat market quiet session",
    ] * 3
    labels = [1, 1, -1, -1, 0, 0] * 3
    sm = SklearnSentiment().fit(texts, labels)
    bull = sm.score("massive rally surge bull buy")
    bear = sm.score("crash plunge bear sell")
    assert bull.value > 0.0
    assert bear.value < 0.0
