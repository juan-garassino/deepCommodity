from __future__ import annotations

import os

_TRUTHY = {"true", "1", "yes", "y", "on"}


def envbool(name: str, default: bool = False) -> bool:
    """Parse an env var as bool, robust to case + surrounding whitespace.

    A stray space (common in web env-var UIs) must not flip a safety flag, so we
    strip + lowercase before comparing. Unset -> default.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUTHY
