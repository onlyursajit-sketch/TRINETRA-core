from __future__ import annotations

from typing import Any

from src.engines.india_vix_engine import (
    IndiaVIXEngine,
    IndiaVIXEngineError,
)
from src.intelligence.market_context import MarketContext


class VIXAdapter:
    """Maps an India VIX payload into MarketContext."""

    def __init__(self) -> None:
        self.engine = IndiaVIXEngine()

    def apply(
        self,
        context: MarketContext,
        payload: dict[str, Any] | None,
    ) -> MarketContext:
        if not isinstance(payload, dict):
            return context

        try:
            result = self.engine.analyse(payload)
        except (
    TypeError,
    ValueError,
    KeyError,
    AssertionError,
    IndiaVIXEngineError,
):
            return context

        value = result.get("current")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            context.vix = float(value)

        return context
