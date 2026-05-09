"""On-chain fetcher — Binance volume-proxy fallback (always available)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "fetch_onchain.py"


def _load():
    spec = importlib.util.spec_from_file_location("fetch_onchain", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_klines(n: int = 30, base_volume: float = 100.0):
    """30 days of synthetic klines, volume[-1] is a 3-sigma outlier."""
    out = []
    for i in range(n):
        ts = (1700000000 + i * 86400) * 1000
        vol = base_volume + (i * 0.5)
        if i == n - 1:
            vol = base_volume * 5  # outlier
        out.append([ts, "0", "0", "0", "0", str(vol), 0, str(vol * 100), 0, 0, 0, 0])
    return out


def test_binance_volume_proxy_basic(monkeypatch):
    mod = _load()

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return _fake_klines(30)

    monkeypatch.setattr(mod.requests, "get", lambda *a, **kw: FakeResp())
    result = mod.fetch_binance_volume_proxy("BTC", 30)
    assert result["asset"] == "BTC"
    assert result["metric"] == "volume_zscore"
    # last bar is 5x baseline -> z-score should be high
    assert result["z_score"] > 1.0
    assert "interpretation" in result


def test_volume_proxy_handles_short_data(monkeypatch):
    mod = _load()

    class FakeResp:
        def raise_for_status(self): pass
        def json(self): return _fake_klines(3)

    monkeypatch.setattr(mod.requests, "get", lambda *a, **kw: FakeResp())
    result = mod.fetch_binance_volume_proxy("BTC", 3)
    # Below 7 daily samples -> only daily series returned, no z-score
    assert "daily" in result


def test_cryptoquant_skipped_without_key(monkeypatch):
    monkeypatch.delenv("CRYPTOQUANT_API_KEY", raising=False)
    mod = _load()
    assert mod.fetch_cryptoquant("BTC", "exchange-reserve", 30) is None


def test_cryptoquant_unknown_metric(monkeypatch):
    monkeypatch.setenv("CRYPTOQUANT_API_KEY", "dummy")
    mod = _load()
    assert mod.fetch_cryptoquant("BTC", "not-a-metric", 30) is None
