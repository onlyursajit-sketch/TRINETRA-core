from __future__ import annotations

import tempfile
import unittest

from src.cache.json_cache import JSONCache
from src.providers.option_chain_factory import (
    ManagedOptionChainCollector,
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
            "nearest_expiry": "17-Jul-2026",
            "underlying_value": 25010,
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


class TestOptionChainFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_live_provider_has_priority(self) -> None:
        manager = create_default_option_chain_manager(
            cache=self.cache,
            collector=FakeLiveCollectorSuccess(),
        )

        result = manager.fetch("nifty")

        self.assertEqual(
            result["provider_used"],
            "NSE",
        )

        self.assertFalse(
            result["fallback_used"]
        )

        self.assertEqual(
            result["data_status"],
            "LIVE",
        )

    def test_json_cache_fallback(self) -> None:
        self.cache.write(
            "option_chain",
            "nifty",
            {
                "symbol": "NIFTY",
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
                "nearest_expiry": "17-Jul-2026",
                "underlying_value": 25010,
                "atm_strike": 25000,
                "source_confidence": 95,
                "data_status": "LIVE",
            },
            ttl_seconds=60,
        )

        collector = ManagedOptionChainCollector(
            cache=self.cache,
            collector=FakeLiveCollectorFailure(),
        )

        result = collector.collect("NIFTY")

        self.assertEqual(
            result["provider_used"],
            "JSON_CACHE",
        )

        self.assertTrue(
            result["fallback_used"]
        )

        self.assertEqual(
            result["data_status"],
            "LIVE",
        )

    def test_all_sources_fail(self) -> None:
        collector = ManagedOptionChainCollector(
            cache=self.cache,
            collector=FakeLiveCollectorFailure(),
        )

        result = collector.collect("NIFTY")

        self.assertEqual(
            result["manager_status"],
            "FAILED",
        )

        self.assertEqual(
            result["data_status"],
            "NO_DATA",
        )

        self.assertEqual(
            result["records"],
            [],
        )

        self.assertEqual(
            len(result["provider_errors"]),
            3,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
