from __future__ import annotations

import unittest

from src.intelligence.market_context import MarketContext
from src.intelligence.regime_engine import RegimeEngine


class TestRegimeEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = RegimeEngine()

    def test_volatile_regime(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            vix=22.0,
        )

        result = self.engine.detect(context)

        self.assertEqual(result, "VOLATILE")
        self.assertEqual(context.regime, "VOLATILE")

    def test_trending_up_regime(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            vix=14.0,
            fii_bias="LONG",
            oi_bullish=True,
        )

        result = self.engine.detect(context)

        self.assertEqual(result, "TRENDING_UP")

    def test_trending_down_regime(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            vix=14.0,
            fii_bias="SHORT",
            oi_bullish=False,
        )

        result = self.engine.detect(context)

        self.assertEqual(result, "TRENDING_DOWN")

    def test_range_regime(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            vix=14.0,
            fii_bias="UNKNOWN",
            oi_bullish=False,
        )

        result = self.engine.detect(context)

        self.assertEqual(result, "RANGE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
