"""API-key auth via X-API-Key header.

Set DC_API_KEY in the env to require the header. If unset, the API is open
(useful for local dev) — never deploy that way to a public endpoint.
"""
from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("DC_API_KEY")
    if not expected:
        return  # open mode; the /health endpoint logs a warning at startup
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing X-API-Key",
        )
