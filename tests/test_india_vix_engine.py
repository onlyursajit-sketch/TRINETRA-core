from __future__ import annotations

import unittest

from src.engines.india_vix_engine import (
    IndiaVIXEngine,
    IndiaVIXEngineError,
)


BASE_PAYLOAD = {
    "symbol": "INDIA_VIX",
    "source": "NSE",
    "source_confidence": 100,
    "data_status": "LIVE",
    "previous_close": 14.20,
    "open": 14.35,
    "high": 15.10,
    "low": 14.05,
    "current": 14.85,
    "timestamp": "2026-07-11T12:00:00+05:30",
}


class TestIndiaVIXEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = IndiaVIXEngine()

    def test_difference_calculation(self) -> None:
        result = self.engine.analyse(
            BASE_PAYLOAD
        )

        self.assertEqual(
            result["difference"],
            0.65,
        )

    def test_percentage_calculation(self) -> None:
        result = self.engine.analyse(
            BASE_PAYLOAD
        )

        self.assertEqual(
            result["percentage_change"],
            4.5775,
        )

    def test_low_risk_regime(self) -> None:
        result = self.engine.analyse(
            BASE_PAYLOAD
        )

        self.assertEqual(
            result["risk_regime"],
            "LOW",
        )

        self.assertEqual(
            result["market_environment"],
            "STABLE",
        )

    def test_rising_direction(self) -> None:
        result = self.engine.analyse(
            BASE_PAYLOAD
        )

        self.assertEqual(
            result["direction"],
            "UP",
        )

        self.assertEqual(
            result["volatility_signal"],
            "RISING",
        )

    def test_very_low_regime(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["current"] = 11.50

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["risk_regime"],
            "VERY_LOW",
        )

    def test_moderate_regime(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["current"] = 16.50

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["risk_regime"],
            "MODERATE",
        )

    def test_high_regime(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["current"] = 21.00

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["risk_regime"],
            "HIGH",
        )

    def test_extreme_regime(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["current"] = 27.00

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["risk_regime"],
            "EXTREME",
        )

    def test_falling_direction(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["previous_close"] = 16.00
        payload["current"] = 14.00

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["direction"],
            "DOWN",
        )

        self.assertEqual(
            result["volatility_signal"],
            "SHARP_FALL",
        )

    def test_stale_confidence(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["data_status"] = "STALE"

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["confidence"],
            "LOW",
        )

    def test_no_data_blocked(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["data_status"] = "NO_DATA"

        with self.assertRaises(
            IndiaVIXEngineError
        ):
            self.engine.analyse(payload)

    def test_invalid_previous_close_blocked(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["previous_close"] = 0

        with self.assertRaises(
            IndiaVIXEngineError
        ):
            self.engine.analyse(payload)

    def test_invalid_current_blocked(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["current"] = None

        with self.assertRaises(
            IndiaVIXEngineError
        ):
            self.engine.analyse(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
