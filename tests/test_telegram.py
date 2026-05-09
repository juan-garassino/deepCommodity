"""Telegram notifier — tests use monkeypatched requests.post (no real network)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "notify_telegram.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("notify_telegram", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _FakeResp:
    def __init__(self, ok=True, status_code=200, text=""):
        self.ok = ok
        self.status_code = status_code
        self.text = text


def test_send_skips_silently_without_env(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    mod = _load_module()
    assert mod.send("hello") is False


def test_send_calls_telegram_api(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["payload"] = json
        return _FakeResp(ok=True)

    mod = _load_module()
    monkeypatch.setattr(mod.requests, "post", fake_post)
    assert mod.send("hello world") is True
    assert "fake_token" in captured["url"]
    assert captured["payload"]["chat_id"] == "12345"
    assert captured["payload"]["text"] == "hello world"
    assert captured["payload"]["parse_mode"] == "HTML"


def test_send_retries_then_fails(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    calls = []

    def fake_post(url, json, timeout):
        calls.append(1)
        return _FakeResp(ok=False, status_code=500, text="boom")

    mod = _load_module()
    monkeypatch.setattr(mod.requests, "post", fake_post)
    monkeypatch.setattr(mod.time, "sleep", lambda *_: None)
    assert mod.send("nope") is False
    assert len(calls) == 3   # 1 + 2 retries


def test_format_includes_topic_and_severity():
    mod = _load_module()
    text = mod._format("trade", "ok", "filled BTC long")
    assert "deepCommodity" in text
    assert "trade" in text
    assert "filled BTC long" in text
    assert text.startswith("✅")  # ok severity prefix


def test_format_truncates_long_body():
    mod = _load_module()
    long_body = "x" * 5000
    text = mod._format(None, "info", long_body)
    assert len(text) <= mod.MAX_LEN + 40
    assert "truncated" in text


def test_main_quiet_exits_zero_on_failure(monkeypatch):
    """--quiet ensures the routine isn't aborted by a Telegram outage."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    mod = _load_module()
    monkeypatch.setattr(sys, "argv",
                        ["notify_telegram", "--message", "x", "--quiet"])
    assert mod.main() == 0


def test_main_returns_nonzero_when_send_fails_without_quiet(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    mod = _load_module()
    monkeypatch.setattr(sys, "argv", ["notify_telegram", "--message", "x"])
    # without --quiet, exit reflects send failure
    assert mod.main() == 1


def test_empty_body_exits_clean(monkeypatch):
    mod = _load_module()
    monkeypatch.setattr(sys, "argv", ["notify_telegram", "--message", "   "])
    assert mod.main() == 0
