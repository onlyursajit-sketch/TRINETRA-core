from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Query

from src.intelligence.context_builder import ContextBuilder
from src.api.live_context import build_live_context


router = APIRouter(
    prefix="/market",
    tags=["Market"],
)

builder = ContextBuilder()


@router.get("/context")
def market_context(
    symbol: str = Query(default="NIFTY", min_length=1),
) -> dict:
    context = build_live_context(builder, symbol)
    return asdict(context)
