from __future__ import annotations

import unittest

from src.providers.option_chain_manager import (
    OptionChainManager,
)
from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class AlwaysFailProvider(
    OptionChainProvider
):
    name = "ALWAYS_FAIL"
    confidence = 0

    def __init__(self) -> None:
        self.calls = 0

    def fetch(self, symbol: str) -> dict:
        self.calls += 1
        raise OptionChainProviderError(
            "Simulated provider failure."
        )


class SuccessProvider(
    OptionChainProvider
):
    name = "SUCCESS"
    confidence = 90

    def fetch(self, symbol: str) -> dict:
        return {
            "symbol": self.clean_symbol(symbol),
            "records": [
                {
                    "strike_price": 25000,
                }
            ],
            "source": self.name,
            "source_confidence": 90,
            "data_status": "LIVE",
        }


class TestProviderCircuitBreaker(
    unittest.TestCase
):
    def test_circuit_opens_after_three_failures(
        self,
    ) -> None:
        failing = AlwaysFailProvider()
        success = SuccessProvider()

        manager = OptionChainManager(
            [
                failing,
                success,
            ]
        )

        for _ in range(3):
            result = manager.fetch("NIFTY")

            self.assertEqual(
                result["provider_used"],
                "SUCCESS",
            )

        self.assertEqual(
            failing.calls,
            3,
        )

        result = manager.fetch("NIFTY")

        self.assertEqual(
            result["provider_used"],
            "SUCCESS",
        )

        self.assertEqual(
            failing.calls,
            3,
        )

        self.assertIn(
            "ALWAYS_FAIL: CIRCUIT_OPEN",
            result["provider_errors"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
