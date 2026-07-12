from __future__ import annotations

import tempfile
import unittest

from src.cache.json_cache import JSONCache
from src.providers.option_chain_factory import (
    create_default_option_chain_manager,
)
from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class FailedLiveCollector:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [],
            "source": "NSE",
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "fallback_reason": "Live unavailable.",
        }


class SuccessfulBrokerProvider(
    OptionChainProvider
):
    name = "BROKER_TEST"
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


class FailedBrokerProvider(
    OptionChainProvider
):
    name = "BROKER_TEST"
    confidence = 90

    def fetch(self, symbol: str) -> dict:
        raise OptionChainProviderError(
            "Broker unavailable."
        )


class TestBrokerPriorityChain(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_broker_used_after_nse_failure(
        self,
    ) -> None:
        manager = create_default_option_chain_manager(
            cache=self.cache,
            collector=FailedLiveCollector(),
            broker_provider=SuccessfulBrokerProvider(),
        )

        result = manager.fetch("nifty")

        self.assertEqual(
            result["provider_used"],
            "BROKER_TEST",
        )

        self.assertTrue(
            result["fallback_used"]
        )

        self.assertEqual(
            result["data_status"],
            "LIVE",
        )

        self.assertEqual(
            len(result["provider_errors"]),
            1,
        )

    def test_cache_used_after_live_and_broker_fail(
        self,
    ) -> None:
        self.cache.write(
            "option_chain",
            "nifty",
            {
                "symbol": "NIFTY",
                "records": [
                    {
                        "strike_price": 25000,
                    }
                ],
                "source_confidence": 95,
                "data_status": "LIVE",
            },
            ttl_seconds=60,
        )

        manager = create_default_option_chain_manager(
            cache=self.cache,
            collector=FailedLiveCollector(),
            broker_provider=FailedBrokerProvider(),
        )

        result = manager.fetch("NIFTY")

        self.assertEqual(
            result["provider_used"],
            "JSON_CACHE",
        )

        self.assertTrue(
            result["fallback_used"]
        )

        self.assertEqual(
            len(result["provider_errors"]),
            2,
        )

    def test_all_three_sources_fail(
        self,
    ) -> None:
        manager = create_default_option_chain_manager(
            cache=self.cache,
            collector=FailedLiveCollector(),
            broker_provider=FailedBrokerProvider(),
        )

        result = manager.fetch("NIFTY")

        self.assertEqual(
            result["manager_status"],
            "FAILED",
        )

        self.assertEqual(
            result["data_status"],
            "NO_DATA",
        )

        self.assertEqual(
            len(result["provider_errors"]),
            3,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
