from __future__ import annotations

import unittest

from src.intelligence.market_context import MarketContext
from src.intelligence.option_chain_context import (
    OptionChainContextAdapter,
)


class TestOptionChainContext(unittest.TestCase):
    def test_apply_maps_option_chain_data(self) -> None:
        context = MarketContext(symbol="NIFTY")

        result = {
            "pcr": {
                "overall_pcr": 1.12,
            },
            "max_pain": {
                "max_pain_strike": 25200,
            },
            "oi": {
                "total_call_oi_change": 120000,
                "total_put_oi_change": 180000,
                "total_call_volume": 90000,
                "total_put_volume": 150000,
            },
        }

        OptionChainContextAdapter().apply(
            context,
            result,
        )

        self.assertEqual(context.pcr, 1.12)
        self.assertEqual(context.max_pain, 25200)
        self.assertTrue(context.oi_bullish)
        self.assertTrue(context.volume_bullish)

    def test_invalid_payload_is_ignored(self) -> None:
        context = MarketContext(symbol="NIFTY")

        OptionChainContextAdapter().apply(
            context,
            None,
        )

        self.assertIsNone(context.pcr)
        self.assertIsNone(context.max_pain)


if __name__ == "__main__":
    unittest.main(verbosity=2)
