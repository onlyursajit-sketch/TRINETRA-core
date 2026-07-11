from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from src.cache.json_cache import (
    JSONCache,
    JSONCacheError,
)


class TestJSONCache(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_write_and_read(self) -> None:
        payload = {
            "symbol": "NIFTY",
            "data_status": "LIVE",
            "value": 25000,
        }

        path = self.cache.write(
            "option_chain",
            "nifty_latest",
            payload,
            ttl_seconds=60,
        )

        self.assertTrue(path.exists())

        result = self.cache.read(
            "option_chain",
            "nifty_latest",
        )

        self.assertIsNotNone(result)
        assert result is not None

        self.assertEqual(
            result["symbol"],
            "NIFTY",
        )

        self.assertFalse(
            result["cache_info"]["is_stale"]
        )

    def test_missing_cache_returns_none(self) -> None:
        result = self.cache.read(
            "pcr",
            "nifty",
        )

        self.assertIsNone(result)

    def test_expired_cache_returns_stale(self) -> None:
        self.cache.write(
            "oi",
            "nifty",
            {
                "data_status": "LIVE",
                "total_call_oi": 1000,
            },
            ttl_seconds=0,
        )

        time.sleep(0.01)

        result = self.cache.read(
            "oi",
            "nifty",
        )

        self.assertIsNotNone(result)
        assert result is not None

        self.assertTrue(
            result["cache_info"]["is_stale"]
        )

        self.assertEqual(
            result["data_status"],
            "STALE",
        )

    def test_stale_blocked_when_disallowed(self) -> None:
        self.cache.write(
            "pcr",
            "nifty",
            {
                "overall_pcr": 1.10,
            },
            ttl_seconds=0,
        )

        time.sleep(0.01)

        result = self.cache.read(
            "pcr",
            "nifty",
            allow_stale=False,
        )

        self.assertIsNone(result)

    def test_atomic_document_structure(self) -> None:
        path = self.cache.write(
            "max_pain",
            "nifty",
            {
                "max_pain_strike": 25000,
            },
            ttl_seconds=120,
        )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            document = json.load(file)

        self.assertIn(
            "cache_metadata",
            document,
        )

        self.assertIn(
            "payload",
            document,
        )

        self.assertEqual(
            document["payload"][
                "max_pain_strike"
            ],
            25000,
        )

    def test_exists(self) -> None:
        self.assertFalse(
            self.cache.exists(
                "india_vix",
                "latest",
            )
        )

        self.cache.write(
            "india_vix",
            "latest",
            {
                "current": 15.5,
            },
        )

        self.assertTrue(
            self.cache.exists(
                "india_vix",
                "latest",
            )
        )

    def test_delete(self) -> None:
        self.cache.write(
            "fii_dii",
            "latest",
            {
                "combined_cash_net": 500,
            },
        )

        deleted = self.cache.delete(
            "fii_dii",
            "latest",
        )

        self.assertTrue(deleted)

        self.assertFalse(
            self.cache.exists(
                "fii_dii",
                "latest",
            )
        )

    def test_clear_namespace(self) -> None:
        self.cache.write(
            "market",
            "snapshot_1",
            {"value": 1},
        )

        self.cache.write(
            "market",
            "snapshot_2",
            {"value": 2},
        )

        deleted = self.cache.clear_namespace(
            "market"
        )

        self.assertEqual(deleted, 2)

    def test_invalid_cache_name_blocked(self) -> None:
        with self.assertRaises(
            JSONCacheError
        ):
            self.cache.write(
                "../unsafe",
                "nifty",
                {"value": 1},
            )

    def test_negative_ttl_blocked(self) -> None:
        with self.assertRaises(
            JSONCacheError
        ):
            self.cache.write(
                "pcr",
                "nifty",
                {"value": 1},
                ttl_seconds=-1,
            )

    def test_non_dictionary_payload_blocked(
        self,
    ) -> None:
        with self.assertRaises(
            JSONCacheError
        ):
            self.cache.write(
                "pcr",
                "nifty",
                ["invalid"],  # type: ignore[arg-type]
            )

    def test_corrupt_cache_blocked(self) -> None:
        path = (
            Path(self.temp_dir.name)
            / "oi"
            / "nifty.json"
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            "{invalid json",
            encoding="utf-8",
        )

        with self.assertRaises(
            JSONCacheError
        ):
            self.cache.read(
                "oi",
                "nifty",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
