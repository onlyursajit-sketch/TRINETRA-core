from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader


api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def require_api_key(
    x_api_key: str | None = Security(api_key_header),
) -> None:
    expected = os.getenv("TRINETRA_API_KEY")

    if expected and x_api_key != expected:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )
