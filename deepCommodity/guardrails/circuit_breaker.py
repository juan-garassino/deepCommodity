from datetime import datetime, timezone
from pathlib import Path

from deepCommodity.guardrails.kill_switch import kill_switch_path

DAILY_DRAWDOWN_THRESHOLD = 0.04
WEEKLY_DRAWDOWN_THRESHOLD = 0.08


def daily_pnl_breach(daily_pnl_pct: float) -> bool:
    return daily_pnl_pct <= -DAILY_DRAWDOWN_THRESHOLD


def weekly_pnl_breach(weekly_pnl_pct: float) -> bool:
    return weekly_pnl_pct <= -WEEKLY_DRAWDOWN_THRESHOLD


def evaluate_drawdown(
    nav: float, baseline: dict, now: datetime
) -> tuple[dict, bool, str]:
    """Compare current NAV to the day/week baseline; decide whether to arm.

    Returns (updated_baseline, should_arm, reason). The first observation of a new
    day/week seeds that period's baseline (no arm). Callers persist the returned
    baseline and arm the kill switch when should_arm is True.
    """
    today = now.strftime("%Y-%m-%d")
    week = now.strftime("%G-W%V")
    new = dict(baseline)
    armed = False
    reasons: list[str] = []

    if baseline.get("daily_date") != today:
        new["daily_date"] = today
        new["daily_nav"] = nav
    else:
        base_nav = float(baseline.get("daily_nav") or 0.0)
        if base_nav > 0:
            dd = (nav - base_nav) / base_nav
            if daily_pnl_breach(dd):
                armed = True
                reasons.append(f"daily drawdown {dd:.2%}")

    if baseline.get("weekly_week") != week:
        new["weekly_week"] = week
        new["weekly_nav"] = nav
    else:
        base_nav = float(baseline.get("weekly_nav") or 0.0)
        if base_nav > 0:
            wd = (nav - base_nav) / base_nav
            if weekly_pnl_breach(wd):
                armed = True
                reasons.append(f"weekly drawdown {wd:.2%}")

    return new, armed, "; ".join(reasons)


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
