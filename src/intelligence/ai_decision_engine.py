from __future__ import annotations

from src.intelligence.market_context import MarketContext


class AIDecisionEngine:
    """Generates BUY/SELL/HOLD decision from market context."""

    def decide(self, context: MarketContext) -> dict:

        score = context.confidence

        if context.fii_bias == "LONG":
            score += 15
        elif context.fii_bias == "SHORT":
            score -= 15

        if context.oi_bullish:
            score += 10
        else:
            score -= 10

        if context.volume_bullish:
            score += 5
        else:
            score -= 5

        if score >= 75:
            action = "BUY"

        elif score <= 30:
            action = "SELL"

        else:
            action = "HOLD"

        return {
            "action": action,
            "score": round(score, 2),
            "confidence": context.confidence,
            "regime": context.regime,
            "fii_bias": context.fii_bias,
        }
