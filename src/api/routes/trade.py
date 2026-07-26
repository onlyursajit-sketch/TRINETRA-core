from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.auth import require_api_key
from src.intelligence.risk_config import RiskConfig
from src.intelligence.trade_plan_engine import TradePlanEngine


router = APIRouter(
    prefix="/trade",
    tags=["Trade"],
)


class TradePlanRequest(BaseModel):
    capital: float = Field(gt=0)
    entry: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    target: float = Field(gt=0)
    risk_per_trade_pct: float = Field(default=1.0, gt=0)
    max_position_pct: float = Field(default=20.0, gt=0)
    min_risk_reward: float = Field(default=2.0, gt=0)


@router.post("/plan")
def create_trade_plan(
    payload: TradePlanRequest,
    _: None = Depends(require_api_key),
) -> dict:
    try:
        config = RiskConfig(
            capital=payload.capital,
            risk_per_trade_pct=payload.risk_per_trade_pct,
            max_position_pct=payload.max_position_pct,
            min_risk_reward=payload.min_risk_reward,
        )

        plan = TradePlanEngine(config).create(
            entry=payload.entry,
            stop_loss=payload.stop_loss,
            target=payload.target,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return asdict(plan)
