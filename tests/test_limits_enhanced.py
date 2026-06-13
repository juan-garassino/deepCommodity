"""Enhanced limit checks added for live-readiness (audit fixes B2/leverage/pyramiding).

These lock behaviors the original check_limits did NOT enforce:
  - per-position cap counts the EXISTING holding of the same symbol (no pyramiding)
  - gross-leverage ceiling (sum of all positions + proposal) / nav
  - finiteness/positivity of qty + notional (NaN/inf/0/negative are blocked)
  - per-bucket daily caps (anchor 1 / theme 2 / gem 1) plus the total cap (3)
"""
from __future__ import annotations

import math

from deepCommodity.guardrails.limits import (
    BUCKET_DAILY_CAPS,
    HARD_LIMITS,
    OrderProposal,
    PortfolioSnapshot,
    check_limits,
)


def _port(nav=10_000.0, cash=10_000.0, positions=None, sector_notional=None,
          new_positions_today=None):
    return PortfolioSnapshot(
        nav_usd=nav,
        cash_usd=cash,
        positions=positions or {},
        sector_notional=sector_notional or {},
        new_positions_today=new_positions_today or {},
    )


# ---- pyramiding: existing holding counts toward the per-position cap ----------

def test_position_cap_counts_existing_holding():
    # already hold 400 (4%); adding 200 (2%) -> 6% of the same symbol > 5% cap
    prop = OrderProposal(symbol="BTC", side="buy", qty=1, notional_usd=200, bucket="anchor")
    ok, reason = check_limits(prop, _port(positions={"BTC": 400.0}))
    assert not ok
    assert "cap" in reason


def test_position_cap_allows_when_total_within_cap():
    # hold 200 (2%) + add 200 (2%) = 4% <= 5%
    prop = OrderProposal(symbol="BTC", side="buy", qty=1, notional_usd=200, bucket="anchor")
    ok, _ = check_limits(prop, _port(positions={"BTC": 200.0}))
    assert ok


# ---- gross leverage -----------------------------------------------------------

def test_gross_leverage_blocks_over_one_x():
    # existing exposure 9_900 + new 200 = 10_100 on 10_000 nav -> 1.01x > 1.0
    prop = OrderProposal(symbol="NEW", side="buy", qty=1, notional_usd=200, bucket="theme")
    ok, reason = check_limits(prop, _port(positions={"ETH": 9_900.0}, cash=100.0))
    assert not ok
    assert "leverage" in reason.lower()


# ---- finiteness / positivity --------------------------------------------------

def test_nan_notional_blocked():
    prop = OrderProposal(symbol="BTC", side="buy", qty=1, notional_usd=float("nan"), bucket="anchor")
    ok, reason = check_limits(prop, _port())
    assert not ok
    assert "invalid" in reason.lower() or "finite" in reason.lower()


def test_inf_notional_blocked():
    prop = OrderProposal(symbol="BTC", side="buy", qty=1, notional_usd=math.inf, bucket="anchor")
    ok, _ = check_limits(prop, _port())
    assert not ok


def test_zero_notional_blocked():
    prop = OrderProposal(symbol="BTC", side="buy", qty=1, notional_usd=0.0, bucket="anchor")
    ok, _ = check_limits(prop, _port())
    assert not ok


def test_negative_notional_blocked():
    prop = OrderProposal(symbol="BTC", side="buy", qty=-1, notional_usd=-100.0, bucket="anchor")
    ok, _ = check_limits(prop, _port())
    assert not ok


# ---- daily caps: total + per-bucket ------------------------------------------

def test_total_daily_cap_blocks_fourth():
    prop = OrderProposal(symbol="NEW", side="buy", qty=1, notional_usd=100, bucket="theme")
    # 3 already opened across buckets -> total cap 3 reached
    port = _port(new_positions_today={"anchor": 1, "theme": 1, "gem": 1})
    ok, reason = check_limits(prop, port)
    assert not ok
    assert "new positions" in reason.lower() or "daily" in reason.lower()


def test_per_bucket_cap_blocks_even_under_total():
    # only 1 opened total, but it was an anchor and anchor cap is 1
    assert BUCKET_DAILY_CAPS["anchor"] == 1
    prop = OrderProposal(symbol="MSFT", side="buy", qty=1, notional_usd=100, bucket="anchor")
    port = _port(new_positions_today={"anchor": 1})
    ok, reason = check_limits(prop, port)
    assert not ok
    assert "anchor" in reason.lower() or "bucket" in reason.lower()


def test_theme_bucket_allows_second():
    # theme cap is 2; one theme opened -> second allowed
    assert BUCKET_DAILY_CAPS["theme"] == 2
    prop = OrderProposal(symbol="NVDA", side="buy", qty=1, notional_usd=100, bucket="theme")
    port = _port(new_positions_today={"theme": 1})
    ok, _ = check_limits(prop, port)
    assert ok


def test_adding_to_existing_position_ignores_daily_caps():
    prop = OrderProposal(symbol="BTC", side="buy", qty=1, notional_usd=100, bucket="anchor")
    port = _port(positions={"BTC": 100.0},
                 new_positions_today={"anchor": 1, "theme": 2})
    ok, _ = check_limits(prop, port)
    assert ok
