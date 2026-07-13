from __future__ import annotations

from src.intelligence.ai_decision_engine import AIDecisionEngine
from src.intelligence.market_context import MarketContext
from src.intelligence.multi_factor_engine import MultiFactorEngine
from src.intelligence.trade_signal import TradeSignal


class TradeSignalEngine:
    """Builds a unified trade signal from market context."""

    def __init__(self) -> None:
        self.decision_engine = AIDecisionEngine()
        self.multi_factor_engine = MultiFactorEngine()

    def generate(self, context: MarketContext) -> TradeSignal:
        decision = self.decision_engine.decide(context)

        reasons: list[str] = []

        if context.fii_bias == "LONG":
            reasons.append("FII bias is bullish")
        elif context.fii_bias == "SHORT":
            reasons.append("FII bias is bearish")

        if context.oi_bullish:
            reasons.append("Open-interest structure is bullish")
        else:
            reasons.append("Open-interest structure is not bullish")

        if context.volume_bullish:
            reasons.append("Options volume supports bullish participation")

        if context.pcr is not None:
            reasons.append(
                f"Put-call ratio is {context.pcr:.2f}"
            )

        if context.vix is not None:
            reasons.append(
                f"India VIX is {context.vix:.2f}"
            )

        risk = 100.0 - context.confidence

        signal = TradeSignal(
            action=decision["action"],
            confidence=context.confidence,
            risk=max(0.0, min(100.0, risk)),
            regime=context.regime,
            fii_bias=context.fii_bias,
            pcr=context.pcr,
            max_pain=context.max_pain,
            reason=reasons,
        )

        signal.confidence = self.multi_factor_engine.evaluate(
            context,
            signal,
        )
        signal.risk = round(100.0 - signal.confidence, 2)

        return signal
