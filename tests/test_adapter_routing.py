"""Paper/live routing + Bitfinex disable (audit fixes B7, alpaca/binance routing).

These are pure env-driven decisions — no SDK/network needed.
"""
from __future__ import annotations

import pytest


# ---- Binance: sandbox unless live AND testnet explicitly false ---------------

def test_binance_sandbox_default_paper(monkeypatch):
    from deepCommodity.execution.binance_adapter import _binance_use_sandbox
    monkeypatch.delenv("BINANCE_TESTNET", raising=False)
    assert _binance_use_sandbox("paper") is True
    assert _binance_use_sandbox("live") is True  # testnet defaults true -> still sandbox


def test_binance_live_real_requires_testnet_false(monkeypatch):
    from deepCommodity.execution.binance_adapter import _binance_use_sandbox
    monkeypatch.setenv("BINANCE_TESTNET", "false")
    assert _binance_use_sandbox("live") is False   # only here does it hit mainnet
    assert _binance_use_sandbox("paper") is True    # paper mode still sandboxes


def test_binance_whitespace_testnet_still_sandbox(monkeypatch):
    from deepCommodity.execution.binance_adapter import _binance_use_sandbox
    monkeypatch.setenv("BINANCE_TESTNET", " true ")  # stray space must not flip it
    assert _binance_use_sandbox("live") is True


# ---- Alpaca: paper unless live AND paper explicitly false --------------------

def test_alpaca_paper_default(monkeypatch):
    from deepCommodity.execution.alpaca_adapter import _alpaca_use_paper
    monkeypatch.delenv("ALPACA_PAPER", raising=False)
    assert _alpaca_use_paper("paper") is True


def test_alpaca_live_without_explicit_false_raises(monkeypatch):
    from deepCommodity.execution.alpaca_adapter import _alpaca_use_paper
    monkeypatch.delenv("ALPACA_PAPER", raising=False)
    with pytest.raises(RuntimeError):
        _alpaca_use_paper("live")  # mismatch: wants live but didn't opt out of paper


def test_alpaca_live_with_explicit_false(monkeypatch):
    from deepCommodity.execution.alpaca_adapter import _alpaca_use_paper
    monkeypatch.setenv("ALPACA_PAPER", "false")
    assert _alpaca_use_paper("live") is False


# ---- Bitfinex disabled in live path -----------------------------------------

def test_bitfinex_disabled_by_default(monkeypatch):
    from deepCommodity.execution.bitfinex_adapter import BitfinexAdapter
    monkeypatch.delenv("BITFINEX_SANDBOX_CONFIRMED", raising=False)
    with pytest.raises(RuntimeError, match="disabled"):
        BitfinexAdapter()
