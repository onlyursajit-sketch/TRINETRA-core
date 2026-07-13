from __future__ import annotations

import unittest

from src.intelligence.ai_decision_engine import AIDecisionEngine
from src.intelligence.market_context import MarketContext


class TestAIDecisionEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = AIDecisionEngine()

    def test_buy_signal(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            confidence=80.0,
            fii_bias="LONG",
            oi_bullish=True,
            volume_bullish=True,
        )

        result = self.engine.decide(context)

        self.assertEqual(result["action"], "BUY")

    def test_sell_signal(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            confidence=20.0,
            fii_bias="SHORT",
            oi_bullish=False,
            volume_bullish=False,
        )

        result = self.engine.decide(context)

        self.assertEqual(result["action"], "SELL")

    def test_hold_signal(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            confidence=50.0,
        )

        result = self.engine.decide(context)

        self.assertEqual(result["action"], "HOLD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
