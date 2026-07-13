from __future__ import annotations

import unittest

from src.intelligence.context_builder import ContextBuilder


class TestContextBuilderVIX(unittest.TestCase):
    def test_vix_payload_updates_context_and_regime(self) -> None:
        vix_payload = {
            "symbol": "INDIA_VIX",
            "previous_close": 18.0,
            "open": 19.0,
            "high": 22.5,
            "low": 18.5,
            "current": 22.0,
            "data_status": "LIVE",
            "source_confidence": 95.0,
        }

        context = ContextBuilder().build(
            symbol="NIFTY",
            vix_payload=vix_payload,
        )

        self.assertEqual(context.vix, 22.0)
        self.assertEqual(context.regime, "VOLATILE")
        self.assertEqual(context.confidence, 50.0)

    def test_missing_vix_payload_keeps_default(self) -> None:
        context = ContextBuilder().build(
            symbol="NIFTY",
        )

        self.assertIsNone(context.vix)


if __name__ == "__main__":
    unittest.main(verbosity=2)
