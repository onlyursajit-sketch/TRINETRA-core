from __future__ import annotations

import unittest

from src.intelligence.context_builder import ContextBuilder


class TestContextBuilderIntegration(unittest.TestCase):
    def test_build_complete_context(self):
        builder = ContextBuilder()

        options = {
            "pcr": {
                "overall_pcr": 1.08,
            },
            "max_pain": {
                "max_pain_strike": 25200,
            },
            "oi": {
                "total_call_oi_change": 100,
                "total_put_oi_change": 200,
                "total_call_volume": 1000,
                "total_put_volume": 2000,
            },
        }

        context = builder.build(
            "NIFTY",
            options,
        )

        self.assertEqual(context.symbol, "NIFTY")
        self.assertEqual(context.pcr, 1.08)
        self.assertEqual(context.max_pain, 25200)
        self.assertTrue(context.oi_bullish)
        self.assertTrue(context.volume_bullish)
        self.assertGreater(context.confidence, 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)
