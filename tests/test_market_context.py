from __future__ import annotations

import unittest

from src.intelligence.confidence_engine import ConfidenceEngine
from src.intelligence.context_builder import ContextBuilder
from src.intelligence.context_validator import (
    ContextValidationError,
    ContextValidator,
)
from src.intelligence.market_context import MarketContext


class TestMarketContext(unittest.TestCase):
    def test_builder_creates_context(self) -> None:
        context = ContextBuilder().build("NIFTY")

        self.assertEqual(context.symbol, "NIFTY")
        self.assertEqual(context.confidence, 50.0)

    def test_validator_accepts_valid_context(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            vix=14.0,
            pcr=1.0,
            confidence=75.0,
        )

        ContextValidator().validate(context)

    def test_validator_rejects_empty_symbol(self) -> None:
        context = MarketContext(symbol="")

        with self.assertRaises(ContextValidationError):
            ContextValidator().validate(context)

    def test_confidence_engine_bullish_context(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            vix=13.0,
            pcr=1.0,
            oi_bullish=True,
            volume_bullish=True,
            fii_bias="LONG",
        )

        score = ConfidenceEngine().calculate(context)

        self.assertEqual(score, 100.0)

    def test_confidence_engine_bearish_context(self) -> None:
        context = MarketContext(
            symbol="NIFTY",
            vix=30.0,
            pcr=1.5,
            fii_bias="SHORT",
        )

        score = ConfidenceEngine().calculate(context)

        self.assertEqual(score, 20.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)


def test_validator_rejects_invalid_institutional_confidence() -> None:
    context = MarketContext(
        symbol="NIFTY",
        institutional_confidence=120.0,
    )

    with unittest.TestCase().assertRaises(ContextValidationError):
        ContextValidator().validate(context)
