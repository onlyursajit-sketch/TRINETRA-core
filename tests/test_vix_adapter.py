from __future__ import annotations

import unittest

from src.intelligence.market_context import MarketContext
from src.intelligence.vix_adapter import VIXAdapter


class TestVIXAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = VIXAdapter()

    def test_valid_payload_updates_context(self) -> None:
        context = MarketContext(symbol="NIFTY")

        payload = {
            "symbol": "INDIA_VIX",
            "previous_close": 14.0,
            "open": 14.1,
            "high": 14.8,
            "low": 13.9,
            "current": 14.5,
            "data_status": "LIVE",
            "source_confidence": 95.0,
        }

        result = self.adapter.apply(context, payload)

        self.assertIs(result, context)
        self.assertEqual(context.vix, 14.5)

    def test_invalid_payload_is_ignored(self) -> None:
        context = MarketContext(symbol="NIFTY")

        result = self.adapter.apply(context, None)

        self.assertIs(result, context)
        self.assertIsNone(context.vix)

    def test_malformed_payload_is_ignored(self) -> None:
        context = MarketContext(symbol="NIFTY")

        result = self.adapter.apply(
            context,
            {"current": "invalid"},
        )

        self.assertIs(result, context)
        self.assertIsNone(context.vix)


if __name__ == "__main__":
    unittest.main(verbosity=2)
