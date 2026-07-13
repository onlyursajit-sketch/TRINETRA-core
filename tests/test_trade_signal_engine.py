from __future__ import annotations

import unittest

from src.intelligence.market_context import MarketContext
from src.intelligence.trade_signal_engine import TradeSignalEngine


class TestTradeSignalEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = TradeSignalEngine()

    def test_generates_buy_signal(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            confidence=85.0,
            regime="TRENDING_UP",
            fii_bias="LONG",
            oi_bullish=True,
            volume_bullish=True,
            pcr=1.10,
            max_pain=25200,
            vix=13.5,
        )

        signal = self.engine.generate(context)

        self.assertEqual(signal.action, "BUY")
        self.assertEqual(signal.confidence, 85.0)
        self.assertEqual(signal.risk, 15.0)
        self.assertEqual(signal.regime, "TRENDING_UP")
        self.assertEqual(signal.fii_bias, "LONG")
        self.assertEqual(signal.pcr, 1.10)
        self.assertEqual(signal.max_pain, 25200)
        self.assertGreater(len(signal.reason), 0)

    def test_generates_sell_signal(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            confidence=20.0,
            regime="TRENDING_DOWN",
            fii_bias="SHORT",
            oi_bullish=False,
            volume_bullish=False,
        )

        signal = self.engine.generate(context)

        self.assertEqual(signal.action, "SELL")
        self.assertEqual(signal.risk, 80.0)

    def test_risk_is_clamped(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            confidence=120.0,
        )

        signal = self.engine.generate(context)

        self.assertEqual(signal.risk, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
