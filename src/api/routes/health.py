from __future__ import annotations

from fastapi import APIRouter
from src.api.version import API_VERSION

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "TRINETRA",
        "version": API_VERSION,
    }
