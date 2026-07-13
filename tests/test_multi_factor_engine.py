from __future__ import annotations

import unittest

from src.intelligence.market_context import MarketContext
from src.intelligence.multi_factor_engine import MultiFactorEngine
from src.intelligence.trade_signal import TradeSignal


class TestMultiFactorEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = MultiFactorEngine()

    def test_bullish_factors_increase_score(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            fii_bias="LONG",
            oi_bullish=True,
            volume_bullish=True,
            regime="TRENDING_UP",
        )

        signal = TradeSignal(
            action="BUY",
            confidence=60.0,
            risk=40.0,
            regime="TRENDING_UP",
            fii_bias="LONG",
            pcr=1.10,
            max_pain=25200,
            reason=[],
        )

        score = self.engine.evaluate(context, signal)

        self.assertEqual(score, 90.0)

    def test_bearish_and_volatile_factors_reduce_score(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            fii_bias="SHORT",
            oi_bullish=False,
            volume_bullish=False,
            regime="VOLATILE",
        )

        signal = TradeSignal(
            action="SELL",
            confidence=50.0,
            risk=50.0,
            regime="VOLATILE",
            fii_bias="SHORT",
            pcr=None,
            max_pain=None,
            reason=[],
        )

        score = self.engine.evaluate(context, signal)

        self.assertEqual(score, 25.0)

    def test_score_is_clamped_at_upper_bound(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            fii_bias="LONG",
            oi_bullish=True,
            volume_bullish=True,
            regime="TRENDING_UP",
        )

        signal = TradeSignal(
            action="BUY",
            confidence=95.0,
            risk=5.0,
            regime="TRENDING_UP",
            fii_bias="LONG",
            pcr=None,
            max_pain=None,
            reason=[],
        )

        score = self.engine.evaluate(context, signal)

        self.assertEqual(score, 100.0)

    def test_score_is_clamped_at_lower_bound(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            fii_bias="SHORT",
            regime="VOLATILE",
        )

        signal = TradeSignal(
            action="SELL",
            confidence=5.0,
            risk=95.0,
            regime="VOLATILE",
            fii_bias="SHORT",
            pcr=None,
            max_pain=None,
            reason=[],
        )

        score = self.engine.evaluate(context, signal)

        self.assertEqual(score, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
