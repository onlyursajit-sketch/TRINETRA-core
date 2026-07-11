from __future__ import annotations

import unittest

from src.engines.oi_engine import (
    OIEngine,
    OIEngineError,
)


OPTION_CHAIN_PAYLOAD = {
    "symbol": "NIFTY",
    "source": "NSE",
    "data_status": "LIVE",
    "underlying_value": 25037.5,
    "atm_strike": 25050,
    "nearest_expiry": "17-Jul-2026",
    "records": [
        {
            "strike_price": 24950,
            "expiry_date": "17-Jul-2026",
            "ce": {
                "openInterest": 1000,
                "changeinOpenInterest": 100,
                "totalTradedVolume": 500,
                "lastPrice": 140.5,
                "change": 12.5,
            },
            "pe": {
                "openInterest": 1200,
                "changeinOpenInterest": 150,
                "totalTradedVolume": 600,
                "lastPrice": 55.5,
                "change": -8.0,
            },
        },
        {
            "strike_price": 25000,
            "expiry_date": "17-Jul-2026",
            "ce": {
                "openInterest": 1800,
                "changeinOpenInterest": 220,
                "totalTradedVolume": 900,
                "lastPrice": 105.0,
                "change": -10.0,
            },
            "pe": {
                "openInterest": 2100,
                "changeinOpenInterest": 300,
                "totalTradedVolume": 1100,
                "lastPrice": 72.0,
                "change": 9.0,
            },
        },
        {
            "strike_price": 25050,
            "expiry_date": "17-Jul-2026",
            "ce": {
                "openInterest": 2300,
                "changeinOpenInterest": 350,
                "totalTradedVolume": 1200,
                "lastPrice": 76.0,
                "change": -6.0,
            },
            "pe": {
                "openInterest": 1700,
                "changeinOpenInterest": -180,
                "totalTradedVolume": 950,
                "lastPrice": 99.0,
                "change": 7.0,
            },
        },
        {
            "strike_price": 25100,
            "expiry_date": "24-Jul-2026",
            "ce": {
                "openInterest": 9999,
                "changeinOpenInterest": 999,
            },
            "pe": {
                "openInterest": 9999,
                "changeinOpenInterest": 999,
            },
        },
    ],
}


class TestOIEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = OIEngine()

    def test_nearest_expiry_only(self) -> None:
        result = self.engine.analyse(
            OPTION_CHAIN_PAYLOAD
        )

        self.assertEqual(
            result["expiry"],
            "17-Jul-2026",
        )
        self.assertEqual(
            result["records_analysed"],
            3,
        )

    def test_total_oi_calculation(self) -> None:
        result = self.engine.analyse(
            OPTION_CHAIN_PAYLOAD
        )

        self.assertEqual(
            result["total_call_oi"],
            5100.0,
        )
        self.assertEqual(
            result["total_put_oi"],
            5000.0,
        )
        self.assertEqual(
            result["total_call_oi_change"],
            670.0,
        )
        self.assertEqual(
            result["total_put_oi_change"],
            270.0,
        )

    def test_support_and_resistance(self) -> None:
        result = self.engine.analyse(
            OPTION_CHAIN_PAYLOAD
        )

        self.assertEqual(
            result["resistance"],
            25050.0,
        )
        self.assertEqual(
            result["support"],
            25000.0,
        )

    def test_buildup_classification(self) -> None:
        result = self.engine.analyse(
            OPTION_CHAIN_PAYLOAD
        )

        summary = result["buildup_summary"]

        self.assertEqual(
            summary["CE_LONG_BUILDUP"],
            1,
        )
        self.assertEqual(
            summary["CE_SHORT_BUILDUP"],
            2,
        )
        self.assertEqual(
            summary["PE_SHORT_BUILDUP"],
            1,
        )
        self.assertEqual(
            summary["PE_LONG_BUILDUP"],
            1,
        )
        self.assertEqual(
            summary["PE_SHORT_COVERING"],
            1,
        )

    def test_no_data_is_blocked(self) -> None:
        payload = {
            "symbol": "NIFTY",
            "data_status": "NO_DATA",
            "records": [],
        }

        with self.assertRaises(OIEngineError):
            self.engine.analyse(payload)

    def test_empty_records_are_blocked(self) -> None:
        payload = {
            "symbol": "NIFTY",
            "data_status": "LIVE",
            "records": [],
        }

        with self.assertRaises(OIEngineError):
            self.engine.analyse(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
