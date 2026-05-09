"""Phase 7: news/sentiment model (specialist).

Three pluggable backends behind a single interface:

    score(text: str) -> SentimentScore(value: float in [-1, 1], confidence: float in [0, 1])

Backends:
    1. RuleBasedSentiment — keyword lexicon, no deps. Ships ready to run.
    2. SklearnSentiment   — TF-IDF + logistic regression, trains when labeled
                            news data is accumulated by the routines.
    3. HuggingFaceSentiment — wraps a finance-tuned classifier (e.g. ProsusAI/finbert).
                              Lazy-imported, opt-in.

Strategy in TRADING-STRATEGY.md picks the backend via env or config.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class SentimentScore:
    value: float       # -1 = strong bear, 0 = neutral, +1 = strong bull
    confidence: float  # 0..1


class SentimentBackend(Protocol):
    name: str
    def score(self, text: str) -> SentimentScore: ...


# ---- 1. rule-based --------------------------------------------------------

BULL_TERMS = {
    "rally", "surge", "soar", "outperform", "breakout", "upgrade", "beat",
    "bullish", "buy", "accumulate", "inflows", "etf approval", "all-time high",
    "ath", "expansion", "growth", "tailwind",
}
BEAR_TERMS = {
    "crash", "plunge", "tumble", "underperform", "breakdown", "downgrade",
    "miss", "bearish", "sell", "outflows", "rejection", "rug", "exploit",
    "hack", "bankruptcy", "halt", "lawsuit", "fud", "headwind", "recession",
}
INTENSIFIERS = {"sharp": 1.3, "massive": 1.5, "modest": 0.7, "slight": 0.6}


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]+", text)]


@dataclass
class RuleBasedSentiment:
    name: str = "rule-based"

    def score(self, text: str) -> SentimentScore:
        if not text:
            return SentimentScore(0.0, 0.0)
        tokens = _tokenize(text)
        bull = sum(1 for t in tokens if t in BULL_TERMS)
        bear = sum(1 for t in tokens if t in BEAR_TERMS)
        # rough intensifier multiplier on the dominant side
        mult = 1.0
        for t, m in INTENSIFIERS.items():
            if t in tokens:
                mult = max(mult, m)
        net = bull - bear
        n = max(1, bull + bear)
        value = max(-1.0, min(1.0, (net / n) * mult))
        # confidence rises with hit count (saturates around 8 hits)
        confidence = min(1.0, (bull + bear) / 8.0)
        return SentimentScore(value=value, confidence=confidence)


# ---- 2. sklearn TF-IDF + LR ----------------------------------------------

class SklearnSentiment:
    """Trained on labeled (text, {-1, 0, 1}) pairs. Trains when data exists."""

    name = "sklearn"

    def __init__(self, model_path: str | Path | None = None):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: F401
            from sklearn.linear_model import LogisticRegression  # noqa: F401
        except ImportError as e:
            raise RuntimeError("scikit-learn not installed; pip install scikit-learn") from e
        self._pipeline = None
        if model_path and Path(model_path).exists():
            self.load(model_path)

    def fit(self, texts: list[str], labels: list[int]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20_000)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ])
        self._pipeline.fit(texts, labels)
        return self

    def score(self, text: str) -> SentimentScore:
        if self._pipeline is None or not text:
            return SentimentScore(0.0, 0.0)
        proba = self._pipeline.predict_proba([text])[0]
        classes = list(self._pipeline.classes_)   # e.g. [-1, 0, 1]
        value = sum(c * p for c, p in zip(classes, proba))
        # confidence = top class margin over uniform
        top = max(proba)
        confidence = max(0.0, min(1.0, (top - 1 / len(classes)) / (1 - 1 / len(classes))))
        return SentimentScore(value=float(value), confidence=float(confidence))

    def save(self, path: str | Path):
        import joblib
        joblib.dump(self._pipeline, path)

    def load(self, path: str | Path):
        import joblib
        self._pipeline = joblib.load(path)


# ---- 3. HuggingFace -------------------------------------------------------

class HuggingFaceSentiment:
    """Wraps a finance-tuned classifier. Opt-in (transformers + model download)."""

    name = "huggingface"

    def __init__(self, model_id: str = "ProsusAI/finbert"):
        try:
            from transformers import pipeline  # type: ignore
        except ImportError as e:
            raise RuntimeError("transformers not installed; pip install transformers torch") from e
        self._pipe = pipeline("sentiment-analysis", model=model_id)

    def score(self, text: str) -> SentimentScore:
        if not text:
            return SentimentScore(0.0, 0.0)
        out = self._pipe(text[:512])[0]
        label = out["label"].lower()
        prob = float(out["score"])
        if "pos" in label or "bull" in label:
            return SentimentScore(value=prob, confidence=prob)
        if "neg" in label or "bear" in label:
            return SentimentScore(value=-prob, confidence=prob)
        return SentimentScore(value=0.0, confidence=prob)


# ---- factory --------------------------------------------------------------

def get_sentiment_backend(name: str | None = None) -> SentimentBackend:
    """Resolve via arg → SENTIMENT_BACKEND env → 'rule-based' default."""
    name = (name or os.getenv("SENTIMENT_BACKEND") or "rule-based").lower()
    if name in ("rule-based", "rules", "lexicon"):
        return RuleBasedSentiment()
    if name == "sklearn":
        return SklearnSentiment(model_path=os.getenv("SENTIMENT_MODEL_PATH"))
    if name in ("huggingface", "hf", "finbert"):
        return HuggingFaceSentiment(os.getenv("SENTIMENT_HF_MODEL", "ProsusAI/finbert"))
    raise ValueError(f"unknown sentiment backend: {name!r}")
