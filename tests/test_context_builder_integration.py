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


def test_context_builder_applies_institutional_flow() -> None:
    from src.intelligence.context_builder import ContextBuilder
    from src.intelligence.institutional_flow import InstitutionalFlow

    flow = InstitutionalFlow(
        fii_cash=1250.0,
        dii_cash=-400.0,
        fii_bias="LONG",
        dii_bias="SHORT",
        confidence=65.0,
    )

    context = ContextBuilder().build(
        symbol="NIFTY",
        institutional_flow=flow,
    )

    assert context.fii_cash == 1250.0
    assert context.dii_cash == -400.0
    assert context.fii_bias == "LONG"
    assert context.dii_bias == "SHORT"
    assert context.institutional_confidence == 65.0
    assert context.confidence == 65.0


def test_context_builder_preserves_institutional_derivatives_flow() -> None:
    from src.intelligence.context_builder import ContextBuilder
    from src.intelligence.institutional_flow import InstitutionalFlow

    flow = InstitutionalFlow(
        fii_cash=-1300.0,
        dii_cash=1600.0,
        fii_index_futures=-750.0,
        fii_stock_futures=420.0,
        fii_bias="SHORT",
        dii_bias="LONG",
        confidence=65.0,
    )

    context = ContextBuilder().build(
        symbol="NIFTY",
        institutional_flow=flow,
    )

    assert context.fii_index_futures == -750.0
    assert context.fii_stock_futures == 420.0
