"""Universe loader — schema invariants on the curated themes.yaml."""
from __future__ import annotations

import pytest
import yaml

from deepCommodity.universe import Universe


def test_default_yaml_loads():
    u = Universe.load()
    assert u.crypto_anchors
    assert u.equity_anchors
    assert u.equity_themes


def test_theme_names_lowercase_underscore_only():
    u = Universe.load()
    for name in u.equity_themes:
        assert name.islower() or "_" in name
        assert name.replace("_", "").isalnum()


def test_no_crypto_symbol_appears_in_two_tiers(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("""
crypto:
  anchors:    [BTC, ETH]
  large_cap:  [SOL, BTC]
  mid_cap:    []
equity:
  anchors:    [SPY]
  themes:
    ai_compute: [NVDA, AMD, AVGO]
""")
    with pytest.raises(ValueError, match="appears in both"):
        Universe.load(bad)


def test_each_theme_has_at_least_three_symbols(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("""
crypto:
  anchors: [BTC]
equity:
  anchors: [SPY]
  themes:
    skinny: [AAA, BBB]
""")
    with pytest.raises(ValueError, match=">= 3 symbols"):
        Universe.load(bad)


def test_anchor_can_appear_in_a_theme(tmp_path):
    """NVDA in both equity.anchors and equity.themes.ai_compute is allowed."""
    ok = tmp_path / "ok.yaml"
    ok.write_text("""
crypto:
  anchors: [BTC]
equity:
  anchors: [SPY, NVDA]
  themes:
    ai_compute: [NVDA, AMD, AVGO]
""")
    u = Universe.load(ok)
    assert "NVDA" in u.equity_anchors
    assert "NVDA" in u.equity_themes["ai_compute"]


def test_symbols_for_theme_raises_on_unknown():
    u = Universe.load()
    with pytest.raises(KeyError, match="unknown theme"):
        u.symbols_for_theme("not-a-theme")


def test_all_themes_in_default_yaml_have_at_least_three_symbols():
    u = Universe.load()
    for name in u.theme_names():
        assert len(u.symbols_for_theme(name)) >= 3, f"theme {name} too small"


def test_invalid_theme_name_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("""
crypto:
  anchors: [BTC]
equity:
  anchors: [SPY]
  themes:
    Bad-Name: [A, B, C]
""")
    with pytest.raises(ValueError, match="theme name"):
        Universe.load(bad)


def test_anchors_required(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("""
crypto:
  anchors: []
equity:
  anchors: [SPY]
  themes:
    x: [A, B, C]
""")
    with pytest.raises(ValueError, match="anchors must be non-empty"):
        Universe.load(bad)


def test_all_tradable_symbols_accessor():
    u = Universe.load()
    crypto = u.all_crypto_symbols()
    equity = u.all_equity_symbols()
    assert "BTC" in crypto and "ETH" in crypto
    assert "SPY" in equity
    assert "VST" in equity   # from ai_power theme
    assert "NVDA" in equity  # from anchors AND ai_compute
