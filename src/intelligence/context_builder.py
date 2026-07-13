from __future__ import annotations

from typing import Any

from src.intelligence.confidence_engine import ConfidenceEngine
from src.intelligence.context_validator import ContextValidator
from src.intelligence.market_context import MarketContext
from src.intelligence.option_chain_context import (
    OptionChainContextAdapter,
)
from src.intelligence.regime_engine import RegimeEngine


class ContextBuilder:
    """Builds and validates a unified market context."""

    def __init__(self) -> None:
        self.option_chain_adapter = OptionChainContextAdapter()
        self.confidence_engine = ConfidenceEngine()
        self.validator = ContextValidator()
        self.regime_engine = RegimeEngine()

    def build(
        self,
        symbol: str,
        options_result: dict[str, Any] | None = None,
    ) -> MarketContext:
        context = MarketContext(symbol=symbol)

        if options_result is not None:
            self.option_chain_adapter.apply(
                context,
                options_result,
            )

        self.regime_engine.detect(context)

        context.confidence = self.confidence_engine.calculate(
            context
        )

        self.validator.validate(context)
        return context
