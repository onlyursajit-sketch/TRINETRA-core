from __future__ import annotations

import unittest

from src.engines.pcr_engine import (
    PCREngine,
    PCREngineError,
)


OI_PAYLOAD = {
    "symbol": "NIFTY",
    "source": "NSE",
    "data_status": "LIVE",
    "expiry": "17-Jul-2026",
    "underlying_value": 25037.5,
    "atm_strike": 25050.0,
    "total_call_oi": 5100.0,
    "total_put_oi": 5000.0,
    "total_call_oi_change": 670.0,
    "total_put_oi_change": 270.0,
    "top_call_oi_levels": [
        {
            "strike": 25050.0,
            "open_interest": 2300.0,
        },
        {
            "strike": 25000.0,
            "open_interest": 1800.0,
        },
        {
            "strike": 24950.0,
            "open_interest": 1000.0,
        },
    ],
    "top_put_oi_levels": [
        {
            "strike": 25000.0,
            "open_interest": 2100.0,
        },
        {
            "strike": 25050.0,
            "open_interest": 1700.0,
        },
        {
            "strike": 24950.0,
            "open_interest": 1200.0,
        },
    ],
}


class TestPCREngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PCREngine()

    def test_overall_pcr(self) -> None:
        result = self.engine.analyse(
            OI_PAYLOAD
        )

        self.assertEqual(
            result["overall_pcr"],
            0.9804,
        )

    def test_oi_change_pcr(self) -> None:
        result = self.engine.analyse(
            OI_PAYLOAD
        )

        self.assertEqual(
            result["oi_change_pcr"],
            0.403,
        )

    def test_atm_pcr(self) -> None:
        result = self.engine.analyse(
            OI_PAYLOAD
        )

        self.assertEqual(
            result["atm_pcr"],
            0.7391,
        )

    def test_strike_wise_pcr(self) -> None:
        result = self.engine.analyse(
            OI_PAYLOAD
        )

        rows = {
            item["strike"]: item
            for item in result["strike_wise_pcr"]
        }

        self.assertEqual(
            rows[24950.0]["pcr"],
            1.2,
        )

        self.assertEqual(
            rows[25000.0]["pcr"],
            1.1667,
        )

        self.assertEqual(
            rows[25050.0]["pcr"],
            0.7391,
        )

    def test_market_interpretation(self) -> None:
        result = self.engine.analyse(
            OI_PAYLOAD
        )

        self.assertEqual(
            result["market_bias"],
            "NEUTRAL_BEARISH",
        )

        self.assertEqual(
            result["signal"],
            "WAIT",
        )

        self.assertEqual(
            result["confidence"],
            "HIGH",
        )

    def test_zero_call_oi(self) -> None:
        payload = dict(OI_PAYLOAD)
        payload["total_call_oi"] = 0

        result = self.engine.analyse(payload)

        self.assertIsNone(
            result["overall_pcr"]
        )

        self.assertEqual(
            result["market_bias"],
            "UNAVAILABLE",
        )

    def test_no_data_blocked(self) -> None:
        payload = dict(OI_PAYLOAD)
        payload["data_status"] = "NO_DATA"

        with self.assertRaises(PCREngineError):
            self.engine.analyse(payload)

    def test_stale_data_confidence(self) -> None:
        payload = dict(OI_PAYLOAD)
        payload["data_status"] = "STALE"

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["confidence"],
            "LOW",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
