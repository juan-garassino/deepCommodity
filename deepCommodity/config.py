"""Centralized runtime configuration access.

One place that reads the process env for the trading-mode and home-directory knobs,
so the gate tools don't each re-implement `os.getenv(...).strip().lower()` and a
`_home()` helper. Whitespace/case-robust by construction.
"""
from __future__ import annotations

import os
from pathlib import Path

from deepCommodity.util import envbool  # re-exported for callers

REPO_ROOT = Path(__file__).resolve().parents[1]

__all__ = ["REPO_ROOT", "dc_home", "trading_mode", "is_live", "is_halt_mode",
           "authorize_live", "max_nav_usd", "envbool"]


def dc_home(override: Path | None = None) -> Path:
    """Home dir for state files (KILL_SWITCH, TRADE-LOG). DC_HOME env, else repo root."""
    return Path(override or os.getenv("DC_HOME") or REPO_ROOT)


def trading_mode() -> str:
    """`paper` (default) | `live` | `halt`, whitespace/case-normalized."""
    return os.getenv("TRADING_MODE", "paper").strip().lower()


def is_live() -> bool:
    return trading_mode() == "live"


def is_halt_mode() -> bool:
    return trading_mode() == "halt"


def authorize_live() -> bool:
    """Second live gate — DAILY_DECISION_AUTHORIZE_LIVE must be explicitly truthy."""
    return envbool("DAILY_DECISION_AUTHORIZE_LIVE", False)


def max_nav_usd() -> float:
    """Live NAV ceiling in USD. 0.0 if unset/invalid — callers fail closed in live mode."""
    raw = os.getenv("DC_MAX_NAV_USD", "").strip()
    try:
        return float(raw)
    except ValueError:
        return 0.0
