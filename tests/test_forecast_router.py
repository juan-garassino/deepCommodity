"""Phase 9 forecast router CLI: dispatch correctly across model backends."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "forecast.py"


def _fixture():
    return {
        "symbols": {
            "BTC": {"price_usd": 60000, "market_cap_usd": 1.2e12,
                    "total_volume_usd": 4e10, "pct_change_24h": 1.2, "pct_change_7d": 5.0},
            "TIA": {"price_usd": 8, "market_cap_usd": 8e8,
                    "total_volume_usd": 1.2e8, "pct_change_24h": -2.0, "pct_change_7d": -8.0},
        }
    }


def _run(*args):
    return subprocess.run([sys.executable, str(TOOL), *args],
                          capture_output=True, text=True)


def test_router_default_is_rule_based(tmp_path):
    p = tmp_path / "fx.json"; p.write_text(json.dumps(_fixture()))
    r = _run("--input", str(p))
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["model"] == "rule-based"
    syms = {f["symbol"] for f in out["forecasts"]}
    assert syms == {"BTC", "TIA"}
    btc = next(f for f in out["forecasts"] if f["symbol"] == "BTC")
    assert btc["direction"] == "long"
    tia = next(f for f in out["forecasts"] if f["symbol"] == "TIA")
    assert tia["direction"] == "short"


def test_router_news_path_returns_flat_with_no_text(tmp_path):
    p = tmp_path / "fx.json"; p.write_text(json.dumps(_fixture()))
    r = _run("--input", str(p), "--model", "news")
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["model"] == "news"
    # No --news-input provided -> empty digest -> flat
    for f in out["forecasts"]:
        assert f["direction"] == "flat"


def test_router_news_path_uses_provided_digest(tmp_path):
    p = tmp_path / "fx.json"; p.write_text(json.dumps(_fixture()))
    n = tmp_path / "n.json"
    n.write_text(json.dumps({"digest": "BTC ETF inflows surge to ATH; massive bullish breakout."}))
    r = _run("--input", str(p), "--model", "news", "--news-input", str(n))
    out = json.loads(r.stdout)
    btc = next(f for f in out["forecasts"] if f["symbol"] == "BTC")
    assert btc["direction"] == "long"


def test_router_ensemble_combines_rule_based_with_news(tmp_path):
    p = tmp_path / "fx.json"; p.write_text(json.dumps(_fixture()))
    n = tmp_path / "n.json"
    n.write_text(json.dumps({"digest": "Bullish breakout, etf approval, all-time high inflows."}))
    r = _run("--input", str(p), "--model", "ensemble", "--news-input", str(n))
    out = json.loads(r.stdout)
    assert out["model"] == "ensemble"
    btc = next(f for f in out["forecasts"] if f["symbol"] == "BTC")
    assert "[ensemble]" in btc["rationale"]
    # rationale should cite rule-based AND news since both contributed
    assert "rule-based" in btc["rationale"] and "news" in btc["rationale"]


def test_router_unknown_model_rejected(tmp_path):
    p = tmp_path / "fx.json"; p.write_text(json.dumps(_fixture()))
    r = _run("--input", str(p), "--model", "magic-eight-ball")
    assert r.returncode != 0


def test_router_no_symbols_errors(tmp_path):
    r = _run("--model", "rule-based")
    assert r.returncode != 0


def test_router_price_skips_when_no_checkpoint(tmp_path):
    """Without a trained checkpoint, the price path produces zero forecasts but exits clean."""
    p = tmp_path / "fx.json"; p.write_text(json.dumps(_fixture()))
    r = _run("--input", str(p), "--model", "price",
             "--bars-dir", str(tmp_path))
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["forecasts"] == []
