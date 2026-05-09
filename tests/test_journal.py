"""journal.py is append-only and must not edit prior entries."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "tools" / "journal.py"


def _run(args, cwd):
    return subprocess.run(
        [sys.executable, str(JOURNAL), *args],
        cwd=cwd, capture_output=True, text=True,
    )


def _scratch(tmp_path: Path) -> Path:
    """Stage a fake repo with empty logs at tmp_path."""
    (tmp_path / "RESEARCH-LOG.md").write_text("# RESEARCH-LOG.md\n\n---\n")
    (tmp_path / "TRADE-LOG.md").write_text("# TRADE-LOG.md\n\n---\n")
    return tmp_path


def test_research_appends_dated_entry(tmp_path, monkeypatch):
    """The journal CLI uses paths anchored to its own location, so we patch globals."""
    scratch = _scratch(tmp_path)
    # Run journal pointing its log paths at the scratch dir via env override
    env = os.environ.copy()
    # journal.py resolves logs relative to its own __file__; we monkeypatch by
    # importing the module and overriding constants in-process.
    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        journal = importlib.import_module("tools.journal") if False else None
    finally:
        sys.path.pop(0)

    # Easier path: import the function and call it with patched paths.
    import importlib.util
    spec = importlib.util.spec_from_file_location("journal", JOURNAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "RESEARCH_LOG", scratch / "RESEARCH-LOG.md")
    monkeypatch.setattr(mod, "TRADE_LOG", scratch / "TRADE-LOG.md")

    # Simulate CLI args
    sys.argv = ["journal", "research", "--topic", "alpha", "--body", "first body"]
    mod.main()
    text1 = (scratch / "RESEARCH-LOG.md").read_text()
    assert "## " in text1 and "alpha" in text1 and "first body" in text1

    sys.argv = ["journal", "research", "--topic", "beta", "--body", "second body"]
    mod.main()
    text2 = (scratch / "RESEARCH-LOG.md").read_text()

    # Append-only: original content survives, new content appended after.
    assert text2.startswith(text1.rstrip()) or text1.rstrip() in text2
    assert "first body" in text2 and "second body" in text2
    assert text2.index("first body") < text2.index("second body")


def test_trade_entry_includes_required_fields(tmp_path, monkeypatch):
    scratch = _scratch(tmp_path)
    import importlib.util
    spec = importlib.util.spec_from_file_location("journal", JOURNAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "TRADE_LOG", scratch / "TRADE-LOG.md")
    monkeypatch.setattr(mod, "RESEARCH_LOG", scratch / "RESEARCH-LOG.md")

    sys.argv = [
        "journal", "trade",
        "--symbol", "BTC", "--side", "buy", "--qty", "0.001",
        "--status", "filled", "--mode", "paper", "--broker", "binance",
        "--order-id", "abc123", "--fill-price", "60000.5",
        "--reason", "rank=0.81 conf=0.78 momentum continuation",
    ]
    mod.main()
    text = (scratch / "TRADE-LOG.md").read_text()
    for needle in ["BTC", "buy", "0.001", "filled", "paper", "binance",
                   "abc123", "60000.5", "rank=0.81"]:
        assert needle in text


def test_invalid_status_rejected(tmp_path):
    res = _run(
        ["trade", "--symbol", "BTC", "--side", "buy", "--qty", "1",
         "--status", "yolo", "--reason", "x"],
        cwd=tmp_path,
    )
    assert res.returncode != 0
    assert "yolo" in res.stderr or "invalid choice" in res.stderr.lower()


def test_invalid_side_rejected(tmp_path):
    res = _run(
        ["trade", "--symbol", "BTC", "--side", "hodl", "--qty", "1",
         "--status", "placed", "--reason", "x"],
        cwd=tmp_path,
    )
    assert res.returncode != 0
