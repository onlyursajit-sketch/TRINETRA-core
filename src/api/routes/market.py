from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Query

from src.intelligence.context_builder import ContextBuilder
from src.api.live_context import build_live_context
from src.providers.option_chain_factory import create_default_option_chain_manager


router = APIRouter(
    prefix="/market",
    tags=["Market"],
)

builder = ContextBuilder()
provider_manager = create_default_option_chain_manager()


@router.get("/context")
def market_context(
    symbol: str = Query(default="NIFTY", min_length=1),
) -> dict:
    context = build_live_context(builder, symbol)
    return asdict(context)

@router.get("/providers/health")
def provider_health() -> dict:
    return {
        "summary": provider_manager.manager_health_summary(),
        "providers": provider_manager.provider_health_report(),
    }

