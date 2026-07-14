from __future__ import annotations

from typing import Any

from src.intelligence.confidence_engine import ConfidenceEngine
from src.intelligence.context_validator import ContextValidator
from src.intelligence.market_context import MarketContext
from src.intelligence.institutional_flow import InstitutionalFlow
from src.intelligence.option_chain_context import (
    OptionChainContextAdapter,
)
from src.intelligence.regime_engine import RegimeEngine
from src.intelligence.vix_adapter import VIXAdapter


class ContextBuilder:
    """Builds and validates a unified market context."""

    def __init__(self) -> None:
        self.option_chain_adapter = OptionChainContextAdapter()
        self.confidence_engine = ConfidenceEngine()
        self.validator = ContextValidator()
        self.regime_engine = RegimeEngine()
        self.vix_adapter = VIXAdapter()

    def build(
        self,
        symbol: str,
        options_result: dict[str, Any] | None = None,
        vix_payload: dict[str, Any] | None = None,
        institutional_flow: InstitutionalFlow | None = None,
    ) -> MarketContext:
        context = MarketContext(symbol=symbol)

        if options_result is not None:
            self.option_chain_adapter.apply(
                context,
                options_result,
            )

        if vix_payload is not None:
            self.vix_adapter.apply(context, vix_payload)

        if institutional_flow is not None:
            context.fii_cash = institutional_flow.fii_cash
            context.dii_cash = institutional_flow.dii_cash
            context.fii_bias = institutional_flow.fii_bias
            context.dii_bias = institutional_flow.dii_bias
            context.institutional_confidence = institutional_flow.confidence

        self.regime_engine.detect(context)

        context.confidence = self.confidence_engine.calculate(
            context
        )

        self.validator.validate(context)
        return context
