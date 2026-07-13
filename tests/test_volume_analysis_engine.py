from __future__ import annotations

import unittest

from src.engines.volume_analysis_engine import (
    VolumeAnalysisEngine,
    VolumeAnalysisError,
)


class TestVolumeAnalysisEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = VolumeAnalysisEngine()

    def test_put_volume_creates_bullish_bias(self) -> None:
        payload = {
            "records": [
                {
                    "strike_price": 25000,
                    "ce": {"totalTradedVolume": 100},
                    "pe": {"totalTradedVolume": 300},
                },
                {
                    "strike_price": 25100,
                    "ce": {"volume": 50},
                    "pe": {"volume": 150},
                },
            ]
        }

        result = self.engine.analyse(payload)

        self.assertEqual(result["call_volume"], 150)
        self.assertEqual(result["put_volume"], 450)
        self.assertEqual(result["market_bias"], "BULLISH")
        self.assertTrue(result["volume_bullish"])
        self.assertEqual(result["analysed_records"], 2)

    def test_empty_volume_is_neutral(self) -> None:
        result = self.engine.analyse({"records": []})

        self.assertEqual(result["market_bias"], "NEUTRAL")
        self.assertFalse(result["volume_bullish"])
        self.assertEqual(result["total_volume"], 0)

    def test_invalid_records_raise_error(self) -> None:
        with self.assertRaises(VolumeAnalysisError):
            self.engine.analyse({"records": "invalid"})


if __name__ == "__main__":
    unittest.main()
