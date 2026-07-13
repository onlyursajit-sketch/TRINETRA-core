from __future__ import annotations

from src.intelligence.market_context import MarketContext
from src.intelligence.trade_signal import TradeSignal


class MultiFactorEngine:
    """Combines all intelligence into a final trade score."""

    def evaluate(
        self,
        context: MarketContext,
        signal: TradeSignal,
    ) -> float:

        score = signal.confidence

        if context.fii_bias == "LONG":
            score += 10
        elif context.fii_bias == "SHORT":
            score -= 10

        if context.oi_bullish:
            score += 8

        if context.volume_bullish:
            score += 5

        if context.regime == "TRENDING_UP":
            score += 7
        elif context.regime == "TRENDING_DOWN":
            score -= 7
        elif context.regime == "VOLATILE":
            score -= 15

        return max(0.0, min(100.0, score))
