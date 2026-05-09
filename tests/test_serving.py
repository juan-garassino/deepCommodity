"""serving/app.py — endpoint surface tests via FastAPI TestClient."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

fastapi_testclient = pytest.importorskip("fastapi.testclient")
TestClient = fastapi_testclient.TestClient


@pytest.fixture
def client(monkeypatch, tmp_path):
    # Open mode (no API key) for these tests
    monkeypatch.delenv("DC_API_KEY", raising=False)
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))   # empty dir = no models
    # Reimport app to pick up env in lifespan
    if "serving.app" in sys.modules:
        del sys.modules["serving.app"]
    if "serving.registry" in sys.modules:
        del sys.modules["serving.registry"]
    from serving.app import app
    with TestClient(app) as c:
        yield c


def test_health_reports_ok_with_no_models(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["available_models"] == {}


def test_rule_based_forecast_works_without_models(client):
    r = client.post("/forecast", json={
        "symbol": "BTC", "model": "rule-based",
        "pct_change_24h": 1.2, "pct_change_7d": 5.0,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["symbol"] == "BTC"
    assert body["direction"] == "long"
    assert body["confidence"] >= 0.5


def test_news_forecast_redacts_injection(client):
    r = client.post("/forecast", json={
        "symbol": "BTC", "model": "news",
        "news_text": "BTC ETF inflows surge to ATH",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["direction"] in ("long", "flat", "short")


def test_price_path_404s_when_no_model(client):
    r = client.post("/forecast", json={
        "symbol": "BTC", "model": "price",
        "bars": {"open": [1, 2], "high": [1, 2], "low": [1, 2],
                 "close": [1, 2], "volume": [1, 1]},
    })
    assert r.status_code == 404


def test_ensemble_with_only_rule_based(client):
    r = client.post("/forecast", json={
        "symbol": "BTC", "model": "ensemble",
        "pct_change_24h": 1.5, "pct_change_7d": 6.0,
    })
    assert r.status_code == 200
    body = r.json()
    assert "rule-based" in body["backends_used"]


def test_ensemble_with_no_signals_422s(client):
    r = client.post("/forecast", json={"symbol": "BTC", "model": "ensemble"})
    assert r.status_code == 422


def test_reload_returns_summary(client):
    r = client.post("/reload")
    assert r.status_code == 200
    assert "reloaded" in r.json()


def test_api_key_enforced_when_set(monkeypatch, tmp_path):
    monkeypatch.setenv("DC_API_KEY", "secret123")
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    if "serving.app" in sys.modules:
        del sys.modules["serving.app"]
    from serving.app import app
    with TestClient(app) as c:
        # /health is open
        assert c.get("/health").status_code == 200
        # /forecast without key
        r = c.post("/forecast", json={
            "symbol": "BTC", "model": "rule-based",
            "pct_change_24h": 1.2, "pct_change_7d": 5.0,
        })
        assert r.status_code == 401
        # with correct key
        r = c.post("/forecast",
                   json={"symbol": "BTC", "model": "rule-based",
                         "pct_change_24h": 1.2, "pct_change_7d": 5.0},
                   headers={"X-API-Key": "secret123"})
        assert r.status_code == 200
        # with wrong key
        r = c.post("/forecast",
                   json={"symbol": "BTC", "model": "rule-based",
                         "pct_change_24h": 1.2, "pct_change_7d": 5.0},
                   headers={"X-API-Key": "wrong"})
        assert r.status_code == 401
