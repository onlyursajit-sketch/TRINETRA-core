from __future__ import annotations

import tempfile
import time
import unittest

from src.cache.json_cache import JSONCache
from src.providers.live.json_cache_provider import (
    JSONCacheOptionChainProvider,
)
from src.providers.option_chain_provider import (
    OptionChainProviderError,
)


class TestJSONCacheOptionChainProvider(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.temp_dir = (
            tempfile.TemporaryDirectory()
        )

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_fresh_cache_fetch(self) -> None:
        self.cache.write(
            "option_chain",
            "nifty",
            {
                "symbol": "NIFTY",
                "records": [
                    {
                        "strike_price": 25000,
                    }
                ],
                "source_confidence": 95,
                "data_status": "LIVE",
            },
            ttl_seconds=60,
        )

        provider = (
            JSONCacheOptionChainProvider(
                cache=self.cache
            )
        )

        result = provider.fetch("nifty")

        self.assertEqual(
            result["source"],
            "JSON_CACHE",
        )

        self.assertEqual(
            result["data_status"],
            "LIVE",
        )

        self.assertEqual(
            result["source_confidence"],
            70.0,
        )

        self.assertTrue(
            result["fallback_source"]
        )

    def test_stale_cache_fetch(self) -> None:
        self.cache.write(
            "option_chain",
            "nifty",
            {
                "symbol": "NIFTY",
                "records": [
                    {
                        "strike_price": 25000,
                    }
                ],
                "source_confidence": 95,
                "data_status": "LIVE",
            },
            ttl_seconds=0,
        )

        time.sleep(0.01)

        provider = (
            JSONCacheOptionChainProvider(
                cache=self.cache,
                allow_stale=True,
            )
        )

        result = provider.fetch("NIFTY")

        self.assertEqual(
            result["data_status"],
            "STALE",
        )

        self.assertEqual(
            result["source_confidence"],
            50.0,
        )

    def test_stale_cache_blocked(self) -> None:
        self.cache.write(
            "option_chain",
            "nifty",
            {
                "records": [
                    {
                        "strike_price": 25000,
                    }
                ]
            },
            ttl_seconds=0,
        )

        time.sleep(0.01)

        provider = (
            JSONCacheOptionChainProvider(
                cache=self.cache,
                allow_stale=False,
            )
        )

        with self.assertRaises(
            OptionChainProviderError
        ):
            provider.fetch("NIFTY")

    def test_missing_cache_blocked(self) -> None:
        provider = (
            JSONCacheOptionChainProvider(
                cache=self.cache
            )
        )

        with self.assertRaises(
            OptionChainProviderError
        ):
            provider.fetch("NIFTY")

    def test_empty_records_blocked(self) -> None:
        self.cache.write(
            "option_chain",
            "nifty",
            {
                "records": [],
            },
            ttl_seconds=60,
        )

        provider = (
            JSONCacheOptionChainProvider(
                cache=self.cache
            )
        )

        with self.assertRaises(
            OptionChainProviderError
        ):
            provider.fetch("NIFTY")


if __name__ == "__main__":
    unittest.main(verbosity=2)
