from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Query

from src.intelligence.context_builder import ContextBuilder


router = APIRouter(
    prefix="/market",
    tags=["Market"],
)

builder = ContextBuilder()


@router.get("/context")
def market_context(
    symbol: str = Query(default="NIFTY", min_length=1),
) -> dict:
    context = builder.build(symbol=symbol)
    return asdict(context)
