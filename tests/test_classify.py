"""classify_symbol maps a symbol to its (bucket, sector) for gate attribution."""
from __future__ import annotations

from deepCommodity.universe import Universe, classify_symbol

U = Universe.load()


def test_equity_anchor_is_anchor_no_sector():
    assert classify_symbol(U, "AAPL") == ("anchor", None)
    assert classify_symbol(U, "SPY") == ("anchor", None)


def test_crypto_anchor_is_anchor():
    assert classify_symbol(U, "BTC") == ("anchor", None)
    assert classify_symbol(U, "ETH") == ("anchor", None)


def test_equity_theme_symbol_maps_to_theme_sector():
    bucket, sector = classify_symbol(U, "NVDA")  # NVDA is also an anchor — anchor wins
    assert bucket == "anchor"
    bucket, sector = classify_symbol(U, "CCJ")   # nuclear theme, not an anchor
    assert bucket == "theme"
    assert sector == "nuclear"


def test_crypto_noncore_is_theme_crypto_sector():
    bucket, sector = classify_symbol(U, "SOL")   # crypto large_cap
    assert bucket == "theme"
    assert sector == "crypto"


def test_unknown_symbol_is_gem():
    assert classify_symbol(U, "WIFHAT9000") == ("gem", None)


def test_case_insensitive():
    assert classify_symbol(U, "aapl") == ("anchor", None)
