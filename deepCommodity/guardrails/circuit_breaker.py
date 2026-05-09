from datetime import datetime, timezone
from pathlib import Path

from deepCommodity.guardrails.kill_switch import kill_switch_path

DAILY_DRAWDOWN_THRESHOLD = 0.04
WEEKLY_DRAWDOWN_THRESHOLD = 0.08


def daily_pnl_breach(daily_pnl_pct: float) -> bool:
    return daily_pnl_pct <= -DAILY_DRAWDOWN_THRESHOLD


def weekly_pnl_breach(weekly_pnl_pct: float) -> bool:
    return weekly_pnl_pct <= -WEEKLY_DRAWDOWN_THRESHOLD


def arm_kill_switch(reason: str, root: Path | None = None,
                    notify: bool = True) -> Path:
    """Create the KILL_SWITCH file with a reason. Idempotent.

    If `notify=True` (default), best-effort Telegram alert. Failures are
    swallowed — the kill switch must arm even if notifications break.
    """
    path = kill_switch_path(root)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path.write_text(f"{stamp}\n{reason}\n")
    if notify:
        try:
            import subprocess
            import sys
            from pathlib import Path as _P
            tool = _P(__file__).resolve().parents[2] / "tools" / "notify_telegram.py"
            subprocess.run([
                sys.executable, str(tool),
                "--topic", "halt", "--severity", "error",
                "--message", f"KILL_SWITCH armed: {reason}", "--quiet",
            ], check=False, timeout=15)
        except Exception:
            pass
    return path
