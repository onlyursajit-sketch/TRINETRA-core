from __future__ import annotations

import unittest

from src.providers.live.nse_provider import (
    NSELiveOptionChainProvider,
)
from src.providers.option_chain_provider import (
    OptionChainProviderError,
)


class FakeCollectorSuccess:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [
                {
                    "strike_price": 25000,
                    "call_oi": 1000,
                    "put_oi": 1200,
                }
            ],
            "source": "NSE",
            "source_confidence": 95,
            "data_status": "LIVE",
        }


class FakeCollectorNoData:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [],
            "source": "NSE",
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "fallback_reason": (
                "403 Forbidden"
            ),
        }


class FakeCollectorFailure:
    def collect(self, symbol: str) -> dict:
        raise RuntimeError(
            "Network unavailable"
        )


class TestNSELiveOptionChainProvider(
    unittest.TestCase
):
    def test_successful_fetch(self) -> None:
        provider = NSELiveOptionChainProvider(
            collector=FakeCollectorSuccess()
        )

        result = provider.fetch("nifty")

        self.assertEqual(
            result["symbol"],
            "NIFTY",
        )

        self.assertEqual(
            result["data_status"],
            "LIVE",
        )

        self.assertEqual(
            len(result["records"]),
            1,
        )

    def test_no_data_is_blocked(self) -> None:
        provider = NSELiveOptionChainProvider(
            collector=FakeCollectorNoData()
        )

        with self.assertRaises(
            OptionChainProviderError
        ):
            provider.fetch("NIFTY")

    def test_collector_failure_is_wrapped(
        self,
    ) -> None:
        provider = NSELiveOptionChainProvider(
            collector=FakeCollectorFailure()
        )

        with self.assertRaises(
            OptionChainProviderError
        ):
            provider.fetch("NIFTY")


if __name__ == "__main__":
    unittest.main(verbosity=2)
