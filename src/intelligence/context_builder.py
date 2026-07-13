from __future__ import annotations

from src.intelligence.confidence_engine import ConfidenceEngine
from src.intelligence.market_context import MarketContext


class ContextBuilder:
    """Builds market context from available analytics."""

    def __init__(self) -> None:
        self.engine = ConfidenceEngine()

    def build(self, symbol: str) -> MarketContext:
        context = MarketContext(symbol=symbol)
        context.confidence = self.engine.calculate(context)
        return context
