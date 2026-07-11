from __future__ import annotations

import unittest

from src.engines.max_pain_engine import (
    MaxPainEngine,
    MaxPainEngineError,
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
            },
            "pe": {
                "openInterest": 1200,
            },
        },
        {
            "strike_price": 25000,
            "expiry_date": "17-Jul-2026",
            "ce": {
                "openInterest": 1800,
            },
            "pe": {
                "openInterest": 2100,
            },
        },
        {
            "strike_price": 25050,
            "expiry_date": "17-Jul-2026",
            "ce": {
                "openInterest": 2300,
            },
            "pe": {
                "openInterest": 1700,
            },
        },
        {
            "strike_price": 25100,
            "expiry_date": "17-Jul-2026",
            "ce": {
                "openInterest": 1300,
            },
            "pe": {
                "openInterest": 800,
            },
        },
        {
            "strike_price": 25200,
            "expiry_date": "24-Jul-2026",
            "ce": {
                "openInterest": 99999,
            },
            "pe": {
                "openInterest": 99999,
            },
        },
    ],
}


class TestMaxPainEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = MaxPainEngine()

    def test_nearest_expiry_filter(self) -> None:
        result = self.engine.analyse(
            OPTION_CHAIN_PAYLOAD
        )

        self.assertEqual(
            result["expiry"],
            "17-Jul-2026",
        )

        self.assertEqual(
            result["strikes_analysed"],
            4,
        )

    def test_max_pain_calculation(self) -> None:
        result = self.engine.analyse(
            OPTION_CHAIN_PAYLOAD
        )

        self.assertEqual(
            result["max_pain_strike"],
            25000.0,
        )

    def test_distance_calculation(self) -> None:
        result = self.engine.analyse(
            OPTION_CHAIN_PAYLOAD
        )

        self.assertEqual(
            result["distance_from_underlying"],
            -37.5,
        )

        self.assertEqual(
            result["distance_from_atm"],
            -50.0,
        )

    def test_pain_table_contains_all_strikes(self) -> None:
        result = self.engine.analyse(
            OPTION_CHAIN_PAYLOAD
        )

        settlement_strikes = {
            row["settlement_strike"]
            for row in result["pain_table"]
        }

        self.assertEqual(
            settlement_strikes,
            {
                24950.0,
                25000.0,
                25050.0,
                25100.0,
            },
        )

    def test_live_confidence(self) -> None:
        result = self.engine.analyse(
            OPTION_CHAIN_PAYLOAD
        )

        self.assertEqual(
            result["confidence"],
            "HIGH",
        )

    def test_stale_confidence(self) -> None:
        payload = dict(OPTION_CHAIN_PAYLOAD)
        payload["data_status"] = "STALE"

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["confidence"],
            "LOW",
        )

    def test_no_data_blocked(self) -> None:
        payload = {
            "symbol": "NIFTY",
            "data_status": "NO_DATA",
            "records": [],
        }

        with self.assertRaises(
            MaxPainEngineError
        ):
            self.engine.analyse(payload)

    def test_empty_records_blocked(self) -> None:
        payload = {
            "symbol": "NIFTY",
            "data_status": "LIVE",
            "records": [],
        }

        with self.assertRaises(
            MaxPainEngineError
        ):
            self.engine.analyse(payload)

    def test_custom_expiry(self) -> None:
        result = self.engine.analyse(
            OPTION_CHAIN_PAYLOAD,
            expiry="24-Jul-2026",
        )

        self.assertEqual(
            result["expiry"],
            "24-Jul-2026",
        )

        self.assertEqual(
            result["strikes_analysed"],
            1,
        )

        self.assertEqual(
            result["max_pain_strike"],
            25200.0,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
