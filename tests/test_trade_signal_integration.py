from __future__ import annotations

import unittest

from src.intelligence.context_builder import ContextBuilder
from src.intelligence.trade_signal_engine import TradeSignalEngine


class TestTradeSignalIntegration(unittest.TestCase):
    def test_option_data_generates_trade_signal(self) -> None:
        options_result = {
            "pcr": {
                "overall_pcr": 1.05,
            },
            "max_pain": {
                "max_pain_strike": 25200,
            },
            "oi": {
                "total_call_oi_change": 100.0,
                "total_put_oi_change": 200.0,
                "total_call_volume": 1000.0,
                "total_put_volume": 2000.0,
            },
        }

        context = ContextBuilder().build(
            symbol="NIFTY",
            options_result=options_result,
        )

        signal = TradeSignalEngine().generate(context)

        self.assertEqual(signal.action, "BUY")
        self.assertEqual(signal.regime, "RANGE")
        self.assertEqual(signal.pcr, 1.05)
        self.assertEqual(signal.max_pain, 25200)
        self.assertGreater(signal.confidence, 50.0)
        self.assertLess(signal.risk, 50.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
