from __future__ import annotations

import tempfile
import unittest

from src.cache.json_cache import JSONCache
from src.collectors.nse_option_chain import NSEOptionChainError
from src.pipelines.options_analytics_pipeline import (
    OptionsAnalyticsPipeline,
)


SAMPLE_OPTION_CHAIN = {
    "records": {
        "underlyingValue": 25037.5,
        "expiryDates": [
            "17-Jul-2026",
            "24-Jul-2026",
        ],
        "data": [
            {
                "strikePrice": 24950,
                "expiryDate": "17-Jul-2026",
                "CE": {
                    "openInterest": 1000,
                    "changeinOpenInterest": 100,
                    "totalTradedVolume": 500,
                    "lastPrice": 140.5,
                    "change": 12.5,
                },
                "PE": {
                    "openInterest": 1200,
                    "changeinOpenInterest": 150,
                    "totalTradedVolume": 600,
                    "lastPrice": 55.5,
                    "change": -8.0,
                },
            },
            {
                "strikePrice": 25000,
                "expiryDate": "17-Jul-2026",
                "CE": {
                    "openInterest": 1800,
                    "changeinOpenInterest": 220,
                    "totalTradedVolume": 900,
                    "lastPrice": 105.0,
                    "change": -10.0,
                },
                "PE": {
                    "openInterest": 2100,
                    "changeinOpenInterest": 300,
                    "totalTradedVolume": 1100,
                    "lastPrice": 72.0,
                    "change": 9.0,
                },
            },
            {
                "strikePrice": 25050,
                "expiryDate": "17-Jul-2026",
                "CE": {
                    "openInterest": 2300,
                    "changeinOpenInterest": 350,
                    "totalTradedVolume": 1200,
                    "lastPrice": 76.0,
                    "change": -6.0,
                },
                "PE": {
                    "openInterest": 1700,
                    "changeinOpenInterest": -180,
                    "totalTradedVolume": 950,
                    "lastPrice": 99.0,
                    "change": 7.0,
                },
            },
        ],
    }
}


class FixtureCollector:
    def __init__(self) -> None:
        from src.collectors.nse_option_chain import (
            NSEOptionChainCollector,
        )

        self.collector = NSEOptionChainCollector()

    def collect(self, symbol: str) -> dict:
        self.collector._validate_response(
            SAMPLE_OPTION_CHAIN
        )

        normalized = self.collector._normalize(
            symbol,
            SAMPLE_OPTION_CHAIN,
        )

        normalized["data_status"] = "LIVE"
        normalized["fallback_reason"] = None
        normalized["cache_path"] = None

        return normalized


class NoDataCollector:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "source": "NSE",
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "fallback_reason": (
                "Simulated source failure."
            ),
            "underlying_value": None,
            "expiry_dates": [],
            "nearest_expiry": None,
            "atm_strike": None,
            "total_records": 0,
            "records": [],
            "cache_path": None,
        }


class TestOptionsAnalyticsPipeline(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_complete_live_pipeline(self) -> None:
        pipeline = OptionsAnalyticsPipeline(
            collector=FixtureCollector(),
            cache=self.cache,
        )

        result = pipeline.run("NIFTY")

        self.assertTrue(
            result["analytics_allowed"]
        )

        self.assertEqual(
            result["data_status"],
            "LIVE",
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

    def test_oi_values(self) -> None:
        pipeline = OptionsAnalyticsPipeline(
            collector=FixtureCollector(),
            cache=self.cache,
        )

        result = pipeline.run("NIFTY")

        assert result["oi"] is not None

        self.assertEqual(
            result["oi"]["total_call_oi"],
            5100.0,
        )

        self.assertEqual(
            result["oi"]["total_put_oi"],
            5000.0,
        )

    def test_pcr_value(self) -> None:
        pipeline = OptionsAnalyticsPipeline(
            collector=FixtureCollector(),
            cache=self.cache,
        )

        result = pipeline.run("NIFTY")

        assert result["pcr"] is not None

        self.assertEqual(
            result["pcr"]["overall_pcr"],
            0.9804,
        )

    def test_max_pain_generated(self) -> None:
        pipeline = OptionsAnalyticsPipeline(
            collector=FixtureCollector(),
            cache=self.cache,
        )

        result = pipeline.run("NIFTY")

        assert result["max_pain"] is not None

        self.assertIn(
            result["max_pain"][
                "max_pain_strike"
            ],
            {
                24950.0,
                25000.0,
                25050.0,
            },
        )

    def test_module_cache_files_created(self) -> None:
        pipeline = OptionsAnalyticsPipeline(
            collector=FixtureCollector(),
            cache=self.cache,
        )

        result = pipeline.run("NIFTY")

        self.assertIsNotNone(
            result["cache_paths"][
                "option_chain"
            ]
        )

        self.assertIsNotNone(
            result["cache_paths"]["oi"]
        )

        self.assertIsNotNone(
            result["cache_paths"]["pcr"]
        )

        self.assertIsNotNone(
            result["cache_paths"][
                "max_pain"
            ]
        )

        self.assertIsNotNone(
            result["cache_paths"][
                "snapshot"
            ]
        )

    def test_no_data_blocks_analytics(self) -> None:
        pipeline = OptionsAnalyticsPipeline(
            collector=NoDataCollector(),
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

        self.assertIsNone(result["oi"])
        self.assertIsNone(result["pcr"])
        self.assertIsNone(
            result["max_pain"]
        )

        self.assertTrue(result["errors"])

    def test_symbol_normalization(self) -> None:
        pipeline = OptionsAnalyticsPipeline(
            collector=FixtureCollector(),
            cache=self.cache,
        )

        result = pipeline.run(" nifty ")

        self.assertEqual(
            result["symbol"],
            "NIFTY",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)


def test_pipeline_includes_volume_and_strike_cluster_analysis() -> None:
    pipeline = OptionsAnalyticsPipeline(
        collector=FixtureCollector(),
        cache=JSONCache(),
    )

    result = pipeline.run("NIFTY")

    assert result["volume_analysis"] is not None
    assert result["volume_analysis"]["analysed_records"] > 0

    assert result["strike_clusters"] is not None
    assert result["strike_clusters"]["cluster_count"] > 0
