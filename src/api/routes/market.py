from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from src.intelligence.context_builder import ContextBuilder
from src.api.live_context import build_live_context
from src.decision.ai_decision import AIDecisionHub
from src.providers.option_chain_factory import create_default_option_chain_manager


router = APIRouter(
    prefix="/market",
    tags=["Market"],
)

builder = ContextBuilder()
provider_manager = create_default_option_chain_manager()


def require_api_key(
    x_api_key: str | None = Header(default=None),
) -> None:
    import os

    expected = os.getenv("TRINETRA_API_KEY")

    if expected and x_api_key != expected:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )


@router.get("/context")
def market_context(
    symbol: str = Query(default="NIFTY", min_length=1),
) -> dict:
    context = build_live_context(builder, symbol)
    return asdict(context)


def build_market_decision(symbol: str) -> dict:
    context = build_live_context(builder, symbol)
    snapshot = asdict(context)
    return AIDecisionHub().decide(snapshot)


@router.get("/decision")
def market_decision(
    symbol: str = Query(default="NIFTY", min_length=1),
    _: None = Depends(require_api_key),
) -> dict:
    return build_market_decision(symbol)

@router.get("/providers/health")
def provider_health() -> dict:
    return {
        "summary": provider_manager.manager_health_summary(),
        "providers": provider_manager.provider_health_report(),
    }

