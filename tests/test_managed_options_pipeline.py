from __future__ import annotations

import tempfile
import unittest

from src.cache.json_cache import JSONCache
from src.pipelines.options_analytics_pipeline import (
    OptionsAnalyticsPipeline,
)
from src.providers.option_chain_factory import (
    ManagedOptionChainCollector,
)


class FakeLiveCollectorFailure:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [],
            "source": "NSE",
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "fallback_reason": "Simulated live source failure.",
        }


class TestManagedOptionsPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_cache_fallback_reaches_analytics_pipeline(
        self,
    ) -> None:
        self.cache.write(
            "option_chain",
            "nifty",
            {
                "symbol": "NIFTY",
                "source": "NSE",
                "source_confidence": 95,
                "data_status": "LIVE",
                "underlying_value": 25010,
                "nearest_expiry": "17-Jul-2026",
                "atm_strike": 25000,
                "records": [
                    {
                        "strike_price": 24950,
                        "expiry_date": "17-Jul-2026",
                        "ce": {
                            "openInterest": 1000,
                            "changeinOpenInterest": 100,
                            "totalTradedVolume": 500,
                            "lastPrice": 120,
                            "change": 5,
                        },
                        "pe": {
                            "openInterest": 1200,
                            "changeinOpenInterest": 150,
                            "totalTradedVolume": 600,
                            "lastPrice": 60,
                            "change": -4,
                        },
                    },
                    {
                        "strike_price": 25000,
                        "expiry_date": "17-Jul-2026",
                        "ce": {
                            "openInterest": 1800,
                            "changeinOpenInterest": 220,
                            "totalTradedVolume": 900,
                            "lastPrice": 90,
                            "change": -6,
                        },
                        "pe": {
                            "openInterest": 2100,
                            "changeinOpenInterest": 300,
                            "totalTradedVolume": 1100,
                            "lastPrice": 75,
                            "change": 7,
                        },
                    },
                    {
                        "strike_price": 25050,
                        "expiry_date": "17-Jul-2026",
                        "ce": {
                            "openInterest": 2300,
                            "changeinOpenInterest": 350,
                            "totalTradedVolume": 1200,
                            "lastPrice": 70,
                            "change": -5,
                        },
                        "pe": {
                            "openInterest": 1700,
                            "changeinOpenInterest": -180,
                            "totalTradedVolume": 950,
                            "lastPrice": 100,
                            "change": 8,
                        },
                    },
                ],
            },
            ttl_seconds=60,
        )

        collector = ManagedOptionChainCollector(
            cache=self.cache,
            collector=FakeLiveCollectorFailure(),
        )

        pipeline = OptionsAnalyticsPipeline(
            collector=collector,
            cache=self.cache,
        )

        result = pipeline.run("NIFTY")

        self.assertTrue(
            result["analytics_allowed"]
        )

        self.assertEqual(
            result["option_chain"]["provider_used"],
            "JSON_CACHE",
        )

        self.assertTrue(
            result["option_chain"]["fallback_used"]
        )

        self.assertIsNotNone(
            result["oi"]
        )
        self.assertIsNotNone(
            result["pcr"]
        )
        self.assertIsNotNone(
            result["max_pain"]
        )

    def test_all_sources_fail_returns_no_data(
        self,
    ) -> None:
        collector = ManagedOptionChainCollector(
            cache=self.cache,
            collector=FakeLiveCollectorFailure(),
        )

        pipeline = OptionsAnalyticsPipeline(
            collector=collector,
            cache=self.cache,
        )

        result = pipeline.run("NIFTY")

        self.assertFalse(
            result["analytics_allowed"]
        )

        self.assertEqual(
            result["data_status"],
            "NO_DATA",
        )

        self.assertIsNone(
            result["oi"]
        )
        self.assertIsNone(
            result["pcr"]
        )
        self.assertIsNone(
            result["max_pain"]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
