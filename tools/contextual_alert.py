#!/usr/bin/env python
"""Read a contextual signal artifact and ping Telegram with the regime + biases.

The contextual model runs off-box (where torch lives) via
`forecast.py --model contextual --out data/macro/contextual_signal.json`; this
tool turns that artifact into a human alert. Shadow mode: informational only —
it does not size or place any order. Silent no-op if Telegram env is unset.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def format_message(payload: dict) -> str:
    regime = payload.get("regime", {})
    emoji = {"EXPANDING": "🟢", "CONTRACTING": "🔴"}.get(regime.get("regime"), "🟡")
    lines = [f"{emoji} macro regime: {regime.get('regime', '?')} (score {regime.get('score', '?')})"]
    d = regime.get("drivers", {})
    lines.append(f"   netliqΔ4w={d.get('netliq_chg4w')} m2_yoy={d.get('m2_yoy')} dxyΔ4w={d.get('dxy_chg4w')}")
    for f in payload.get("forecasts", []):
        h = f.get("horizons", {})
        wk, dl = h.get("weekly", {}), h.get("daily", {})
        lines.append(f"   {f['symbol']}: 2wk {wk.get('direction')}/{wk.get('confidence')}"
                     f" · 1-3d {dl.get('direction')}/{dl.get('confidence')}")
    lines.append("(shadow — informational, not sizing trades)")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--signal", default=str(ROOT / "data" / "macro" / "contextual_signal.json"))
    args = p.parse_args()
    path = Path(args.signal)
    if not path.exists():
        sys.exit(f"signal not found: {path}")
    payload = json.loads(path.read_text())
    msg = format_message(payload)
    print(msg)
    subprocess.run([sys.executable, str(ROOT / "tools" / "notify_telegram.py"),
                    "--topic", "contextual", "--severity", "info", "--message", msg, "--quiet"],
                   timeout=30)


if __name__ == "__main__":
    main()
