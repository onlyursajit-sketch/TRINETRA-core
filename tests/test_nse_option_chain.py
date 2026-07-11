from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.collectors.nse_option_chain import (
    NSEOptionChainCollector,
    NSEOptionChainError,
)


SAMPLE_RESPONSE = {
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
                },
                "PE": {
                    "openInterest": 1200,
                    "changeinOpenInterest": 150,
                    "totalTradedVolume": 600,
                    "lastPrice": 55.5,
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
                },
                "PE": {
                    "openInterest": 2100,
                    "changeinOpenInterest": 300,
                    "totalTradedVolume": 1100,
                    "lastPrice": 72.0,
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
                },
                "PE": {
                    "openInterest": 1700,
                    "changeinOpenInterest": 180,
                    "totalTradedVolume": 950,
                    "lastPrice": 99.0,
                },
            },
        ],
    }
}


class LiveFixtureCollector(NSEOptionChainCollector):
    def _fetch_raw(self, symbol: str) -> dict:
        return SAMPLE_RESPONSE


class FailedCollector(NSEOptionChainCollector):
    def _fetch_raw(self, symbol: str) -> dict:
        raise NSEOptionChainError("Simulated NSE failure")


class TestNSEOptionChainCollector(unittest.TestCase):
    def test_symbol_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = NSEOptionChainCollector(cache_dir=temp_dir)

            self.assertEqual(
                collector._validate_symbol(" nifty "),
                "NIFTY",
            )

            with self.assertRaises(ValueError):
                collector._validate_symbol("INVALID")

    def test_normalization_and_atm(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = NSEOptionChainCollector(cache_dir=temp_dir)

            result = collector._normalize(
                "NIFTY",
                SAMPLE_RESPONSE,
            )

            self.assertEqual(result["symbol"], "NIFTY")
            self.assertEqual(result["underlying_value"], 25037.5)
            self.assertEqual(result["atm_strike"], 25050)
            self.assertEqual(result["nearest_expiry"], "17-Jul-2026")
            self.assertEqual(result["total_records"], 3)

    def test_live_collection_and_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = LiveFixtureCollector(cache_dir=temp_dir)

            result = collector.collect("NIFTY")

            self.assertEqual(result["data_status"], "LIVE")
            self.assertEqual(result["source_confidence"], 100)
            self.assertEqual(result["total_records"], 3)

            latest_cache = Path(temp_dir) / "nifty_latest.json"

            self.assertTrue(latest_cache.exists())

            with latest_cache.open("r", encoding="utf-8") as file:
                cached = json.load(file)

            self.assertEqual(cached["symbol"], "NIFTY")
            self.assertEqual(cached["data_status"], "LIVE")

    def test_stale_cache_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            latest_cache = Path(temp_dir) / "nifty_latest.json"

            cached_payload = {
                "symbol": "NIFTY",
                "source": "NSE",
                "source_confidence": 100,
                "underlying_value": 25000,
                "expiry_dates": ["17-Jul-2026"],
                "nearest_expiry": "17-Jul-2026",
                "atm_strike": 25000,
                "total_records": 1,
                "records": [],
            }

            with latest_cache.open("w", encoding="utf-8") as file:
                json.dump(cached_payload, file)

            collector = FailedCollector(cache_dir=temp_dir)
            result = collector.collect("NIFTY")

            self.assertEqual(result["data_status"], "STALE")
            self.assertEqual(result["underlying_value"], 25000)
            self.assertIn(
                "Serving last valid cached snapshot",
                result["fallback_reason"],
            )

    def test_no_data_without_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            collector = FailedCollector(cache_dir=temp_dir)

            result = collector.collect("NIFTY")

            self.assertEqual(result["data_status"], "NO_DATA")
            self.assertEqual(result["source_confidence"], 0)
            self.assertEqual(result["total_records"], 0)
            self.assertEqual(result["records"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
