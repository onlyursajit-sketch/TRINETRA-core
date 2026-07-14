from __future__ import annotations

import unittest

from src.collectors.india_vix_collector import (
    IndiaVIXCollector,
    IndiaVIXCollectorError,
)


class TestIndiaVIXCollector(unittest.TestCase):
    def test_collect_maps_yahoo_payload(self) -> None:
        def fake_fetcher(symbol: str) -> dict:
            self.assertEqual(symbol, "^INDIAVIX")
            return {
                "previous_close": 14.5,
                "open": 14.7,
                "high": 15.1,
                "low": 14.2,
                "current": 14.85,
                "source_timestamp": "2026-07-14T08:30:00+00:00",
                "source": "Yahoo",
            }

        result = IndiaVIXCollector(fake_fetcher).collect()

        self.assertEqual(result["symbol"], "INDIA_VIX")
        self.assertEqual(result["current"], 14.85)
        self.assertEqual(result["data_status"], "STALE")
        self.assertEqual(result["source_confidence"], 70)

    def test_invalid_current_raises_error(self) -> None:
        collector = IndiaVIXCollector(
            lambda symbol: {"current": None}
        )

        with self.assertRaises(IndiaVIXCollectorError):
            collector.collect()


if __name__ == "__main__":
    unittest.main()
