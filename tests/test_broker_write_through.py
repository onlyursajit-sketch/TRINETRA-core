from __future__ import annotations

import tempfile
import unittest

from src.cache.json_cache import JSONCache
from src.providers.option_chain_factory import (
    create_default_option_chain_manager,
)
from src.providers.option_chain_provider import (
    OptionChainProvider,
)


class FailedLiveCollector:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [],
            "source": "NSE",
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "fallback_reason": "NSE unavailable.",
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


class TestBrokerWriteThrough(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_broker_success_updates_cache(self) -> None:
        manager = create_default_option_chain_manager(
            cache=self.cache,
            collector=FailedLiveCollector(),
            broker_provider=SuccessfulBrokerProvider(),
        )

        result = manager.fetch("NIFTY")

        self.assertEqual(
            result["provider_used"],
            "BROKER_TEST",
        )

        self.assertEqual(
            result["cache_wrapper"],
            "WRITE_THROUGH",
        )

        self.assertTrue(
            result["fallback_used"]
        )

        self.assertTrue(
            result["write_through_cache"]
        )

        cached = self.cache.read(
            namespace="option_chain",
            key="nifty",
            allow_stale=True,
        )

        self.assertIsNotNone(cached)

        self.assertEqual(
            cached["source"],
            "BROKER_TEST",
        )

        self.assertEqual(
            len(cached["records"]),
            1,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
