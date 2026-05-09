#!/usr/bin/env python
"""Send a Telegram message via the Bot API. No framework, no dependencies beyond requests.

Setup (one-time):
  1. DM @BotFather on Telegram, run /newbot, save the token.
  2. DM your new bot once, then visit
       https://api.telegram.org/bot<TOKEN>/getUpdates
     to get your numeric chat ID from `from.id`.
  3. Put both into .env:
       TELEGRAM_BOT_TOKEN=...
       TELEGRAM_CHAT_ID=...

Usage:
  python tools/notify_telegram.py --message "ETH long opened at 3120, conviction 0.78"
  python tools/notify_telegram.py --topic trade --severity info --message "..."
  cat report.md | python tools/notify_telegram.py --topic weekly-review --stdin

Severity is purely cosmetic (prefix emoji): info | ok | warn | error.
Errors writing to Telegram are logged to stderr but never crash the caller —
the routine should keep running even when the network is down.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
SEVERITY_PREFIX = {
    "info": "🔵", "ok": "✅", "warn": "⚠️", "error": "❌",
    "trade": "💱", "research": "🔎", "weekly": "📊", "halt": "🛑",
}
MAX_LEN = 4000  # Telegram caps at 4096; leave headroom for HTML escaping


def _format(topic: str | None, severity: str, body: str) -> str:
    prefix = SEVERITY_PREFIX.get(severity, "•")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    head = f"{prefix} <b>deepCommodity</b>"
    if topic:
        head += f" / <code>{topic}</code>"
    head += f"\n<i>{stamp}</i>\n"
    text = head + "\n" + body
    if len(text) > MAX_LEN:
        text = text[: MAX_LEN - 30] + "\n…<i>(truncated)</i>"
    return text


def send(text: str, *, token: str | None = None, chat_id: str | None = None,
         retries: int = 2) -> bool:
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("notify_telegram: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set; skipping",
              file=sys.stderr)
        return False
    url = TELEGRAM_API.format(token=token)
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }, timeout=10)
            if r.ok:
                return True
            print(f"notify_telegram: HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"notify_telegram: attempt {attempt+1}: {e}", file=sys.stderr)
        if attempt < retries:
            time.sleep(0.5 * (attempt + 1))
    return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--message", help="message body (or use --stdin)")
    p.add_argument("--stdin", action="store_true", help="read body from stdin")
    p.add_argument("--topic", default=None,
                   help="short label, e.g. research / trade / weekly-review / halt")
    p.add_argument("--severity", default="info",
                   choices=list(SEVERITY_PREFIX.keys()))
    p.add_argument("--quiet", action="store_true",
                   help="exit 0 even if delivery failed (default true; flag preserved for clarity)")
    args = p.parse_args()

    body = sys.stdin.read() if args.stdin else (args.message or "")
    if not body.strip():
        print("notify_telegram: empty body, nothing to send", file=sys.stderr)
        return 0

    text = _format(args.topic, args.severity, body.strip())
    ok = send(text)
    return 0 if ok or args.quiet else 1


if __name__ == "__main__":
    sys.exit(main())
