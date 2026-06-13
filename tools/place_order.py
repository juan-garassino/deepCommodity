#!/usr/bin/env python
"""Submit an order to Binance (crypto) or Alpaca (equity).

Every order passes through preflight() — the single code-enforced gate. Gates, in order:
  1. KILL_SWITCH / DC_HALT / TRADING_MODE=halt   -> exit 2   (fail-closed halt)
  2. live authorization: TRADING_MODE=live AND
     DAILY_DECISION_AUTHORIZE_LIVE=true AND --confirm-live   -> exit 3 if unmet
  3. buys require --allow-buy (position-mgmt never opens)     -> exit 5
  4. preflight: authoritative broker snapshot + all limits    -> exit 1 (blocked/unavailable)
  5. live NAV must be <= DC_MAX_NAV_USD ceiling               -> exit 3
Then broker.submit with a deterministic client_order_id (idempotency). exit 0 ok / 4 reject.
The notional is sized from the BROKER's reference price, never a trusted --price.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.execution.broker import OrderRequest, get_broker  # noqa: E402
from deepCommodity.execution.portfolio import (  # noqa: E402
    BrokerPortfolioProvider,
    PortfolioUnavailable,
)
from deepCommodity.guardrails.kill_switch import halt_state  # noqa: E402
from deepCommodity.guardrails.preflight import preflight  # noqa: E402
from deepCommodity.guardrails.limits import OrderProposal  # noqa: E402
from deepCommodity.universe import Universe, classify_symbol  # noqa: E402
from deepCommodity.util import envbool  # noqa: E402


def _home(home: Path | None = None) -> Path:
    return Path(home or os.getenv("DC_HOME") or ROOT)


def _journal(symbol, side, qty, status, result, reason, mode) -> None:
    cmd = [
        sys.executable, str(ROOT / "tools" / "journal.py"), "trade",
        "--symbol", symbol, "--side", side, "--qty", str(qty),
        "--status", status, "--mode", mode,
        "--broker", str(result.get("broker", "-")),
        "--order-id", str(result.get("order_id") or ""),
        "--fill-price", str(result.get("fill_price") or ""),
        "--reason", reason,
    ]
    subprocess.run(cmd, check=False)
    severity = {"filled": "ok", "placed": "info", "rejected": "error",
                "blocked": "warn", "skipped": "info"}.get(status, "info")
    body = (f"{status.upper()} {side} {qty} {symbol} "
            f"@ {result.get('fill_price') or '-'}  ({mode})\nreason: {reason}")
    subprocess.run([
        sys.executable, str(ROOT / "tools" / "notify_telegram.py"),
        "--topic", "trade", "--severity", severity, "--message", body, "--quiet",
    ], check=False)


def _make_provider_and_broker(asset_class: str, home: Path):
    """Build the live broker + authoritative portfolio provider. May raise."""
    broker = get_broker(asset_class)
    provider = BrokerPortfolioProvider(
        broker, Universe.load(), trade_log_path=_home(home) / "TRADE-LOG.md"
    )
    return provider, broker


def _client_order_id(symbol, side, qty, reason, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    raw = f"{symbol}|{side}|{qty}|{reason}|{now.strftime('%Y-%m-%d')}"
    return "dc-" + hashlib.sha256(raw.encode()).hexdigest()[:24]


def _live_authorized(mode: str, confirm_live: bool) -> tuple[bool, str]:
    if mode != "live":
        return True, ""
    if not envbool("DAILY_DECISION_AUTHORIZE_LIVE", False):
        return False, "live requires DAILY_DECISION_AUTHORIZE_LIVE=true and --confirm-live"
    if not confirm_live:
        return False, "live requires --confirm-live"
    return True, ""


def execute(
    *,
    symbol: str,
    side: str,
    qty: float,
    asset_class: str,
    reason: str,
    price: float | None = None,
    type: str = "market",
    limit_price: float | None = None,
    sector: str | None = None,
    allow_buy: bool = False,
    confirm_live: bool = False,
    provider=None,
    broker=None,
    home: Path | None = None,
) -> int:
    mode = os.getenv("TRADING_MODE", "paper").strip().lower()
    symbol = symbol.strip().upper()  # canonical key — must match broker position keys

    def block(status_reason: str, result: dict | None = None) -> None:
        _journal(symbol, side, qty, "blocked", result or {}, status_reason, mode)

    # Gate 1: halt (first, fail-closed)
    halted, confirmed, hreason = halt_state(root=_home(home))
    if halted or not confirmed:
        print(f"BLOCKED: halt ({hreason})", file=sys.stderr)
        block(f"halt: {hreason}")
        return 2

    # Gate 2: live authorization
    ok, why = _live_authorized(mode, confirm_live)
    if not ok:
        print(f"BLOCKED: {why}", file=sys.stderr)
        block(why)
        return 3

    # Gate 3: buy permission (position-mgmt never passes --allow-buy)
    if side == "buy" and not allow_buy:
        print("BLOCKED: buys require --allow-buy in this context", file=sys.stderr)
        block("buy without --allow-buy")
        return 5

    # Build broker + provider (fail-closed on init error)
    if provider is None or broker is None:
        try:
            provider, broker = _make_provider_and_broker(asset_class, _home(home))
        except Exception as e:  # noqa: BLE001
            print(f"BLOCKED: broker/provider unavailable ({e})", file=sys.stderr)
            block(f"broker unavailable: {e}")
            return 1

    # Size notional from the BROKER reference price (never trust --price for buys).
    try:
        ref = broker.reference_price(symbol)
    except Exception:  # noqa: BLE001
        ref = None
    if side == "buy":
        if not ref or ref <= 0:
            print("BLOCKED: no broker reference price for buy sizing", file=sys.stderr)
            block("no broker reference price")
            return 1
        notional = qty * ref
    else:
        # sells reduce exposure and skip the buy-only caps; sizing is informational
        notional = qty * (ref or (price if price and price > 0 else 0.0))

    bucket, derived_sector = classify_symbol(Universe.load(), symbol)
    proposal = OrderProposal(
        symbol=symbol, side=side, qty=qty, notional_usd=notional,
        sector=sector or derived_sector, bucket=bucket,
    )

    # Gate 4: preflight (halt re-check + authoritative snapshot + all limits)
    decision = preflight(proposal, provider, root=_home(home))
    if not decision.allow:
        print(decision.reason, file=sys.stderr)
        block(decision.reason)
        return 2 if decision.code == "halt" else 1

    # Gate 5: live NAV ceiling — fail CLOSED if the ceiling is unset/invalid
    if mode == "live":
        try:
            ceiling = float(os.getenv("DC_MAX_NAV_USD", "").strip())
        except ValueError:
            ceiling = 0.0
        if ceiling <= 0:
            msg = "live requires a positive DC_MAX_NAV_USD ceiling"
            print(f"BLOCKED: {msg}", file=sys.stderr)
            block(msg)
            return 3
        nav = decision.snapshot.nav_usd if decision.snapshot else float("inf")
        if nav > ceiling:
            msg = f"live NAV {nav:.0f} exceeds DC_MAX_NAV_USD ceiling {ceiling:.0f}"
            print(f"BLOCKED: {msg}", file=sys.stderr)
            block(msg)
            return 3

    # Submit
    req = OrderRequest(
        symbol=symbol, side=side, qty=qty, asset_class=asset_class, type=type,
        limit_price=limit_price,
        client_order_id=_client_order_id(symbol, side, qty, reason),
    )
    result = broker.submit(req)
    payload = {
        "ok": result.ok, "broker": result.broker, "mode": result.mode,
        "symbol": result.symbol, "side": result.side, "qty": result.qty,
        "fill_price": result.fill_price, "order_id": result.order_id,
        "error": result.error,
    }
    print(json.dumps(payload, indent=2))
    if result.ok:
        status = "filled" if result.fill_price else "placed"
    else:
        status = "rejected"
    _journal(symbol, side, qty, status, payload,
             reason + (f" | error={result.error}" if not result.ok else ""), mode)
    return 0 if result.ok else 4


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", required=True)
    p.add_argument("--side", required=True, choices=["buy", "sell"])
    p.add_argument("--qty", required=True, type=float)
    p.add_argument("--price", type=float, default=0.0,
                   help="fallback reference price (USD) if the broker can't quote")
    p.add_argument("--asset-class", required=True, choices=["crypto", "equity"])
    p.add_argument("--type", default="market", choices=["market", "limit"])
    p.add_argument("--limit-price", type=float, default=None)
    p.add_argument("--sector", default=None)
    p.add_argument("--reason", required=True, help="why this trade (free text, journaled)")
    p.add_argument("--allow-buy", action="store_true",
                   help="required to OPEN/add a position; position-mgmt never sets it")
    p.add_argument("--confirm-live", action="store_true",
                   help="required when TRADING_MODE=live")
    args = p.parse_args()
    code = execute(
        symbol=args.symbol, side=args.side, qty=args.qty,
        asset_class=args.asset_class, reason=args.reason, price=args.price,
        type=args.type, limit_price=args.limit_price, sector=args.sector,
        allow_buy=args.allow_buy, confirm_live=args.confirm_live,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
