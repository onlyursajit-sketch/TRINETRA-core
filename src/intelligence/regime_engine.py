from __future__ import annotations

from src.intelligence.market_context import MarketContext


class RegimeEngine:
    """Detects current market regime."""

    def detect(
        self,
        context: MarketContext,
    ) -> str:

        if context.vix is not None and context.vix >= 20:
            context.regime = "VOLATILE"
            return context.regime

        if (
            context.fii_bias == "LONG"
            and context.oi_bullish
        ):
            context.regime = "TRENDING_UP"

        elif (
            context.fii_bias == "SHORT"
            and not context.oi_bullish
        ):
            context.regime = "TRENDING_DOWN"

        else:
            context.regime = "RANGE"

        return context.regime
