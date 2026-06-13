"""API-key auth via X-API-Key header.

Fail-closed: if DC_API_KEY is unset, protected endpoints refuse (503) UNLESS the
operator explicitly opts into open mode for local dev with DC_ALLOW_OPEN=true.
A forecast endpoint that can steer real trades must not be reachable unauthenticated
by accident.
"""
from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException, status


def _allow_open() -> bool:
    return os.getenv("DC_ALLOW_OPEN", "").strip().lower() in {"true", "1", "yes"}


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("DC_API_KEY")
    if not expected:
        if _allow_open():
            return  # explicit local-dev opt-in
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DC_API_KEY not set; refusing (set DC_ALLOW_OPEN=true for local dev only)",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing X-API-Key",
        )
