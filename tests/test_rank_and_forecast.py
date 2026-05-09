"""Test the small-cap thesis and the v1 rule-based forecaster."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _fixture():
    return {
        "symbols": {
            "BTC":  {"price_usd": 60000, "market_cap_usd": 1.2e12,
                     "total_volume_usd": 4e10, "pct_change_24h": 1.0, "pct_change_7d": 5.0},
            "TIA":  {"price_usd": 8,     "market_cap_usd": 8e8,
                     "total_volume_usd": 1.2e8, "pct_change_24h": 4.0, "pct_change_7d": 18.0},
            "INJ":  {"price_usd": 30,    "market_cap_usd": 3e9,
                     "total_volume_usd": 5e8,  "pct_change_24h": 3.5, "pct_change_7d": 12.0},
            "MEGA": {"price_usd": 100,   "market_cap_usd": 8e11,
                     "total_volume_usd": 1e10, "pct_change_24h": 0.1, "pct_change_7d": 0.5},
        }
    }


def _run(tool, args):
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / tool), *args],
        capture_output=True, text=True,
    )


def test_smallcap_outranks_megacap(tmp_path):
    p = tmp_path / "fx.json"
    p.write_text(json.dumps(_fixture()))
    r = _run("rank_smallcaps.py", ["--input", str(p), "--top", "4"])
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    syms = [row["symbol"] for row in out["ranked"]]
    # TIA is smallest cap with strongest momentum -> #1
    assert syms[0] == "TIA"
    # MEGA is biggest with weakest momentum -> last
    assert syms[-1] == "MEGA"


def test_rank_weights_sum_to_one(tmp_path):
    p = tmp_path / "fx.json"
    p.write_text(json.dumps(_fixture()))
    r = _run("rank_smallcaps.py",
             ["--input", str(p), "--w-momentum", "2", "--w-mcap", "2", "--w-volume", "1"])
    out = json.loads(r.stdout)
    assert abs(sum(out["weights"].values()) - 1.0) < 1e-9


def test_rank_filters_missing_mcap(tmp_path):
    bad = {"symbols": {"X": {"price_usd": 1, "pct_change_7d": 5}}}  # no market_cap
    p = tmp_path / "bad.json"; p.write_text(json.dumps(bad))
    r = _run("rank_smallcaps.py", ["--input", str(p)])
    out = json.loads(r.stdout)
    assert out["ranked"] == []


def test_forecast_long_on_concordant_momentum(tmp_path):
    p = tmp_path / "fx.json"
    p.write_text(json.dumps(_fixture()))
    r = _run("forecast.py", ["--input", str(p), "--symbols", "TIA"])
    out = json.loads(r.stdout)
    f = out["forecasts"][0]
    assert f["symbol"] == "TIA"
    assert f["direction"] == "long"
    assert f["confidence"] >= 0.6


def test_forecast_short_on_concordant_breakdown(tmp_path):
    fx = {"symbols": {"X": {"price_usd": 10, "market_cap_usd": 1e9,
                            "total_volume_usd": 1e6,
                            "pct_change_24h": -2.0, "pct_change_7d": -8.0}}}
    p = tmp_path / "x.json"; p.write_text(json.dumps(fx))
    r = _run("forecast.py", ["--input", str(p)])
    f = json.loads(r.stdout)["forecasts"][0]
    assert f["direction"] == "short"


def test_forecast_flat_on_mixed_signal(tmp_path):
    fx = {"symbols": {"X": {"price_usd": 10, "market_cap_usd": 1e9,
                            "total_volume_usd": 1e6,
                            "pct_change_24h": -0.2, "pct_change_7d": 0.4}}}
    p = tmp_path / "x.json"; p.write_text(json.dumps(fx))
    r = _run("forecast.py", ["--input", str(p)])
    f = json.loads(r.stdout)["forecasts"][0]
    assert f["direction"] == "flat"


def test_forecast_mean_reversion_after_capitulation(tmp_path):
    fx = {"symbols": {"X": {"price_usd": 10, "market_cap_usd": 1e9,
                            "total_volume_usd": 1e6,
                            "pct_change_24h": 0.5, "pct_change_7d": -15.0}}}
    p = tmp_path / "x.json"; p.write_text(json.dumps(fx))
    r = _run("forecast.py", ["--input", str(p)])
    f = json.loads(r.stdout)["forecasts"][0]
    assert f["direction"] == "long"
    assert "mean-reversion" in f["rationale"]
