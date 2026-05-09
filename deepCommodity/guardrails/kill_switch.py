from pathlib import Path

KILL_SWITCH_FILENAME = "KILL_SWITCH"


def kill_switch_path(root: Path | None = None) -> Path:
    return (root or Path.cwd()) / KILL_SWITCH_FILENAME


def is_armed(root: Path | None = None) -> bool:
    return kill_switch_path(root).exists()
