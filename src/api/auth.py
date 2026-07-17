from __future__ import annotations

import os

from fastapi import Header, HTTPException


def require_api_key(
    x_api_key: str | None = Header(default=None),
) -> None:
    expected = os.getenv("TRINETRA_API_KEY")

    if expected and x_api_key != expected:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )
