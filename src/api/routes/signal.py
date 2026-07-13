from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Query

from src.intelligence.context_builder import ContextBuilder
from src.intelligence.trade_signal_engine import TradeSignalEngine

router = APIRouter(
    prefix="/signal",
    tags=["Signal"],
)

builder = ContextBuilder()
engine = TradeSignalEngine()


@router.get("")
def signal(
    symbol: str = Query(default="NIFTY", min_length=1),
) -> dict:
    context = builder.build(symbol=symbol)
    trade_signal = engine.generate(context)
    return asdict(trade_signal)
