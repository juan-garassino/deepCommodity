from __future__ import annotations

import os
from pathlib import Path

from deepCommodity.util import envbool

KILL_SWITCH_FILENAME = "KILL_SWITCH"
# Anchor to the repo root, NOT the process CWD — a routine that cd's elsewhere must
# still find an armed switch (audit fix B6).
REPO_ROOT = Path(__file__).resolve().parents[2]


def kill_switch_path(root: Path | None = None) -> Path:
    return (root or REPO_ROOT) / KILL_SWITCH_FILENAME


def is_armed(root: Path | None = None) -> bool:
    return kill_switch_path(root).exists()


def halt_state(root: Path | None = None) -> tuple[bool, bool, str]:
    """Return (halted, confirmed, reason).

    Fail-closed contract: callers must treat `not confirmed` as halted. Halt is
    armed by ANY of: DC_HALT env, TRADING_MODE=halt (out-of-band, reaches cloud
    routines on next run), or the repo-root KILL_SWITCH file (local).
    """
    try:
        if envbool("DC_HALT", False):
            return True, True, "DC_HALT env set"
        if os.getenv("TRADING_MODE", "").strip().lower() == "halt":
            return True, True, "TRADING_MODE=halt"
        if is_armed(root):
            return True, True, "KILL_SWITCH file present"
        return False, True, "not halted"
    except Exception as e:  # cannot determine -> caller fails closed
        return True, False, f"halt-state unconfirmable: {e}"
