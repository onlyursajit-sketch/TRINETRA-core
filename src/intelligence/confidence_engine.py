from __future__ import annotations

from src.intelligence.market_context import MarketContext


class ConfidenceEngine:
    """Calculates an overall market confidence score."""

    def calculate(self, context: MarketContext) -> float:
        score = 50.0

        if context.oi_bullish:
            score += 10

        if context.volume_bullish:
            score += 10

        if context.fii_bias.upper() == "LONG":
            score += 15
        elif context.fii_bias.upper() == "SHORT":
            score -= 15

        if context.pcr is not None:
            if 0.8 <= context.pcr <= 1.2:
                score += 10
            else:
                score -= 5

        if context.vix is not None:
            if context.vix < 15:
                score += 5
            elif context.vix > 25:
                score -= 10

        return max(0.0, min(100.0, score))
