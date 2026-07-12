from __future__ import annotations

import tempfile
import unittest

from src.cache.json_cache import JSONCache
from src.providers.option_chain_factory import (
    create_default_option_chain_manager,
)


class FakeLiveCollectorSuccess:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [
                {
                    "strike_price": 25000,
                    "expiry_date": "17-Jul-2026",
                    "ce": {
                        "openInterest": 1000,
                    },
                    "pe": {
                        "openInterest": 1200,
                    },
                }
            ],
            "underlying_value": 25010,
            "nearest_expiry": "17-Jul-2026",
            "atm_strike": 25000,
            "source": "NSE",
            "source_confidence": 95,
            "data_status": "LIVE",
        }


class FakeLiveCollectorFailure:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [],
            "source": "NSE",
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "fallback_reason": "Simulated live failure.",
        }


class TestWriteThroughFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_live_success_writes_cache(self) -> None:
        manager = create_default_option_chain_manager(
            cache=self.cache,
            collector=FakeLiveCollectorSuccess(),
        )

        result = manager.fetch("NIFTY")

        self.assertEqual(
            result["provider_used"],
            "NSE",
        )

        self.assertEqual(
            result["cache_wrapper"],
            "WRITE_THROUGH",
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
            cached["symbol"],
            "NIFTY",
        )

    def test_live_failure_uses_written_cache(self) -> None:
        first_manager = (
            create_default_option_chain_manager(
                cache=self.cache,
                collector=FakeLiveCollectorSuccess(),
            )
        )

        first_manager.fetch("NIFTY")

        second_manager = (
            create_default_option_chain_manager(
                cache=self.cache,
                collector=FakeLiveCollectorFailure(),
            )
        )

        result = second_manager.fetch("NIFTY")

        self.assertEqual(
            result["provider_used"],
            "JSON_CACHE",
        )

        self.assertTrue(
            result["fallback_used"]
        )

        self.assertEqual(
            len(result["records"]),
            1,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
