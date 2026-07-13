from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "TRINETRA",
        "version": "1.0.0",
    }
