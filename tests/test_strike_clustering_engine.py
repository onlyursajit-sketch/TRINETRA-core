from __future__ import annotations

import unittest

from src.engines.strike_clustering_engine import (
    StrikeClusteringEngine,
    StrikeClusteringError,
)


class TestStrikeClusteringEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = StrikeClusteringEngine()

    def test_detects_support_and_resistance_clusters(self) -> None:
        payload = {
            "records": [
                {
                    "strike_price": 25000,
                    "ce": {"openInterest": 100, "volume": 50},
                    "pe": {"openInterest": 500, "volume": 150},
                },
                {
                    "strike_price": 25050,
                    "ce": {"openInterest": 100, "volume": 25},
                    "pe": {"openInterest": 300, "volume": 75},
                },
                {
                    "strike_price": 25200,
                    "ce": {"openInterest": 600, "volume": 200},
                    "pe": {"openInterest": 100, "volume": 50},
                },
            ]
        }

        result = self.engine.analyse(
            payload,
            cluster_size=100,
        )

        self.assertEqual(result["cluster_count"], 2)
        self.assertEqual(
            result["strongest_support"]["cluster_start"],
            25000,
        )
        self.assertEqual(
            result["strongest_resistance"]["cluster_start"],
            25200,
        )

    def test_empty_records_returns_empty_result(self) -> None:
        result = self.engine.analyse({"records": []})

        self.assertEqual(result["cluster_count"], 0)
        self.assertEqual(result["top_clusters"], [])
        self.assertIsNone(result["strongest_support"])

    def test_invalid_cluster_size_raises_error(self) -> None:
        with self.assertRaises(StrikeClusteringError):
            self.engine.analyse(
                {"records": []},
                cluster_size=0,
            )


if __name__ == "__main__":
    unittest.main()
