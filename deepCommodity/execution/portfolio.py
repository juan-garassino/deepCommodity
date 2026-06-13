"""Authoritative portfolio state for the pre-trade gate.

The risk gate reads NAV, positions (USD notional), and cash straight from the broker —
never a stubbed or fabricated snapshot. Any broker error raises PortfolioUnavailable so
the caller fails CLOSED (audit fix B3). Today's new-position counts come from our own
append-only TRADE-LOG.md (we are its only writer); bucket/sector attribution is derived
deterministically from the universe (audit fix B2/sector).
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from deepCommodity.guardrails.limits import PortfolioSnapshot
from deepCommodity.universe import Universe, classify_symbol

TRADE_LOG_DEFAULT = Path(__file__).resolve().parents[2] / "TRADE-LOG.md"

_HEADER_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})")
_FIELD_RE = re.compile(r"^-\s*(\w+):\s*(.+?)\s*$")


class PortfolioUnavailable(Exception):
    """Raised when authoritative portfolio state cannot be obtained. Fail closed."""


def count_new_positions_today(
    trade_log_path: Path,
    universe: Universe,
    today: str,
) -> dict[str, int]:
    """Count distinct symbols with a FILLED buy logged today, grouped by bucket.

    Conservative: a same-day add to an existing holding also counts (errs toward
    blocking, never toward over-trading). Missing/unreadable log -> empty (no fills).
    """
    try:
        text = Path(trade_log_path).read_text(encoding="utf-8")
    except OSError:
        return {}

    seen: set[str] = set()
    counts: dict[str, int] = {}
    cur_date: str | None = None
    fields: dict[str, str] = {}

    def _flush() -> None:
        if cur_date != today:
            return
        # count any successful submission toward the daily cap — a market order that
        # the broker accepted but hasn't reported a fill price for is logged "placed",
        # and must still consume a daily slot (else the cap is evadable).
        if fields.get("status", "").lower() not in ("filled", "placed"):
            return
        if fields.get("side", "").lower() != "buy":
            return
        sym = fields.get("symbol", "").strip().upper()
        if not sym or sym in seen:
            return
        seen.add(sym)
        bucket, _ = classify_symbol(universe, sym)
        counts[bucket] = counts.get(bucket, 0) + 1

    for line in text.splitlines():
        m = _HEADER_RE.match(line)
        if m:
            _flush()
            cur_date = m.group(1)
            fields = {}
            continue
        fm = _FIELD_RE.match(line)
        if fm:
            fields[fm.group(1).lower()] = fm.group(2)
    _flush()
    return counts


class PortfolioProvider(ABC):
    @abstractmethod
    def snapshot(self) -> PortfolioSnapshot: ...


class BrokerPortfolioProvider(PortfolioProvider):
    def __init__(
        self,
        broker,
        universe: Universe,
        now: datetime | None = None,
        trade_log_path: Path | None = None,
    ) -> None:
        self.broker = broker
        self.universe = universe
        self._now = now
        self._trade_log_path = trade_log_path or TRADE_LOG_DEFAULT

    def snapshot(self) -> PortfolioSnapshot:
        try:
            nav, raw_positions, cash = self.broker.account_state()
            nav = float(nav)
            # upper-case keys so the gate's per-position/pyramiding lookups match
            # regardless of how the symbol was typed on the CLI
            positions = {str(k).upper(): float(v) for k, v in raw_positions.items()}
            cash = float(cash)
        except PortfolioUnavailable:
            raise
        except Exception as e:  # any broker/SDK failure -> fail closed
            raise PortfolioUnavailable(f"broker state unavailable: {e}") from e

        sector_notional: dict[str, float] = {}
        for sym, notional in positions.items():
            _, sector = classify_symbol(self.universe, sym)
            if sector:
                sector_notional[sector] = sector_notional.get(sector, 0.0) + notional

        now = self._now or datetime.now(timezone.utc)
        new_today = count_new_positions_today(
            self._trade_log_path, self.universe, now.strftime("%Y-%m-%d")
        )

        return PortfolioSnapshot(
            nav_usd=nav,
            cash_usd=cash,
            positions=positions,
            sector_notional=sector_notional,
            new_positions_today=new_today,
            as_of=now,
            source=getattr(self.broker, "name", "broker"),
        )


class MockPortfolioProvider(PortfolioProvider):
    """In-repo mock — returns a supplied snapshot or raises (for tests)."""

    def __init__(self, snapshot: PortfolioSnapshot | None = None,
                 raises: Exception | None = None) -> None:
        self._snapshot = snapshot
        self._raises = raises

    def snapshot(self) -> PortfolioSnapshot:
        if self._raises is not None:
            raise self._raises
        if self._snapshot is None:
            raise PortfolioUnavailable("no snapshot configured")
        return self._snapshot


def make_provider(
    asset_class: str,
    *,
    home: Path | None = None,
    now: datetime | None = None,
    universe: Universe | None = None,
):
    """The single provider+broker factory for the gate path.

    Returns (provider, broker). Broker construction failure raises PortfolioUnavailable
    so callers fail closed. `universe` lets a caller load themes.yaml once and share it.
    """
    from deepCommodity.config import dc_home
    from deepCommodity.execution.broker import get_broker

    try:
        broker = get_broker(asset_class)
    except Exception as e:
        raise PortfolioUnavailable(f"broker init failed: {e}") from e
    provider = BrokerPortfolioProvider(
        broker,
        universe or Universe.load(),
        now=now,
        trade_log_path=dc_home(home) / "TRADE-LOG.md",
    )
    return provider, broker


def build_snapshot(asset_class: str, now: datetime | None = None) -> PortfolioSnapshot:
    """Wire the live broker + universe into an authoritative snapshot. Fail closed."""
    provider, _ = make_provider(asset_class, now=now)
    return provider.snapshot()
