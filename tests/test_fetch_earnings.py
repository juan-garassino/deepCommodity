"""Earnings calendar fetcher — Finnhub + yfinance fallback."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "fetch_earnings.py"


def _load():
    spec = importlib.util.spec_from_file_location("fetch_earnings", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SAMPLE_FINNHUB = {
    "earningsCalendar": [
        {"symbol": "NVDA", "date": "2026-05-15", "hour": "amc",
         "year": 2026, "quarter": 1, "epsEstimate": 0.85, "epsActual": None,
         "revenueEstimate": 26000000000, "revenueActual": None},
        {"symbol": "AAPL", "date": "2026-05-22", "hour": "amc",
         "year": 2026, "quarter": 2, "epsEstimate": 1.55, "epsActual": None,
         "revenueEstimate": 95000000000, "revenueActual": None},
    ]
}


def test_finnhub_returns_empty_without_key(monkeypatch):
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    mod = _load()
    assert mod.fetch_finnhub([], 14) == []


def test_finnhub_fetches_with_key(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "dummy")
    mod = _load()

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return SAMPLE_FINNHUB

    monkeypatch.setattr(mod.requests, "get", lambda *a, **kw: FakeResp())
    rows = mod.fetch_finnhub([], 14)
    assert len(rows) == 2
    assert rows[0]["symbol"] == "NVDA"


def test_finnhub_filters_by_symbols(monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "dummy")
    mod = _load()

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return SAMPLE_FINNHUB

    monkeypatch.setattr(mod.requests, "get", lambda *a, **kw: FakeResp())
    rows = mod.fetch_finnhub(["NVDA"], 14)
    assert len(rows) == 1
    assert rows[0]["symbol"] == "NVDA"
