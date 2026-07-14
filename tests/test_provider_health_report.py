import unittest

from src.providers.option_chain_manager import OptionChainManager
from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class FailingProvider(OptionChainProvider):
    name = "FAILING"

    def fetch(self, symbol: str) -> dict:
        raise OptionChainProviderError("Simulated failure.")


class SuccessProvider(OptionChainProvider):
    name = "SUCCESS"

    def fetch(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [{"strike_price": 25000}],
            "source": self.name,
            "source_confidence": 90,
            "data_status": "LIVE",
        }


class TestProviderHealthReport(unittest.TestCase):
    def test_health_report(self) -> None:
        manager = OptionChainManager(
            [FailingProvider(), SuccessProvider()]
        )

        manager.fetch("NIFTY")

        report = manager.provider_health_report()

        self.assertEqual(
            report["FAILING"]["failure_count"],
            1,
        )

        self.assertEqual(
            report["SUCCESS"]["success_count"],
            1,
        )

        self.assertTrue(
            report["SUCCESS"]["available"]
        )

        self.assertEqual(
            report["FAILING"]["success_rate"],
            0.0,
        )

        self.assertEqual(
            report["SUCCESS"]["success_rate"],
            100.0,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)


def test_health_report_preserves_providers_with_same_wrapper_name() -> None:
    from src.providers.option_chain_manager import OptionChainManager

    class FakeProvider:
        name = "WRITE_THROUGH"
        confidence = 90

        def fetch(self, symbol: str) -> dict:
            return {
                "symbol": symbol,
                "records": [],
                "source": "TEST",
                "data_status": "NO_DATA",
            }

    first = FakeProvider()
    second = FakeProvider()

    manager = OptionChainManager(
        providers=[first, second],
    )

    report = manager.provider_health_report()

    assert len(report) == 2
