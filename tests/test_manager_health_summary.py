import unittest

from src.providers.option_chain_manager import OptionChainManager
from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class FailProvider(OptionChainProvider):
    name = "FAIL"

    def fetch(self, symbol: str) -> dict:
        raise OptionChainProviderError("Failure")


class SuccessProvider(OptionChainProvider):
    name = "SUCCESS"

    def fetch(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [{"strike_price": 25000}],
            "source": "SUCCESS",
            "source_confidence": 95,
            "data_status": "LIVE",
        }


class TestManagerHealthSummary(unittest.TestCase):

    def test_summary(self):
        manager = OptionChainManager(
            [
                FailProvider(),
                SuccessProvider(),
            ]
        )

        manager.fetch("NIFTY")

        summary = manager.manager_health_summary()

        self.assertEqual(summary["status"], "HEALTHY")
        self.assertEqual(summary["providers_total"], 2)
        self.assertEqual(summary["providers_available"], 2)
        self.assertEqual(summary["providers_unavailable"], 0)
        self.assertGreaterEqual(
            summary["overall_success_rate"],
            50.0,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
