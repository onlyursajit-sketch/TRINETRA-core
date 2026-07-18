from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from src.intelligence.context_builder import ContextBuilder
from src.api.live_context import build_live_context
from src.api.auth import require_api_key
from src.decision.ai_decision import AIDecisionHub
from src.providers.option_chain_factory import create_default_option_chain_manager
from src.pipelines.options_analytics_pipeline import OptionsAnalyticsPipeline


router = APIRouter(
    prefix="/market",
    tags=["Market"],
)

builder = ContextBuilder()
provider_manager = create_default_option_chain_manager()
options_pipeline = OptionsAnalyticsPipeline()



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

@router.get("/option-chain")
def market_option_chain(
    symbol: str = Query(default="NIFTY", min_length=1),
) -> dict:
    clean_symbol = symbol.strip().upper()
    snapshot = options_pipeline.run(clean_symbol)

    option_chain = snapshot.get("option_chain") or {}
    pcr = snapshot.get("pcr") or {}
    max_pain = snapshot.get("max_pain") or {}
    oi = snapshot.get("oi") or {}
    volume_analysis = snapshot.get("volume_analysis") or {}

    return {
        **option_chain,
        "symbol": clean_symbol,
        "pcr": pcr.get("overall_pcr"),
        "pcr_bias": pcr.get("market_bias"),
        "max_pain": max_pain.get("max_pain_strike"),
        "oi_bias": oi.get("market_bias"),
        "volume_bias": volume_analysis.get("market_bias"),
        "analytics_allowed": snapshot.get("analytics_allowed", False),
        "analytics_errors": snapshot.get("errors", []),
    }


@router.get("/providers/health")
def provider_health() -> dict:
    return {
        "summary": provider_manager.manager_health_summary(),
        "providers": provider_manager.provider_health_report(),
    }

