from __future__ import annotations

import tempfile
import unittest

from src.cache.json_cache import JSONCache
from src.providers.live.write_through_provider import (
    WriteThroughOptionChainProvider,
)
from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class FakeLiveProvider(
    OptionChainProvider
):
    name = "FAKE_LIVE"
    confidence = 95

    def fetch(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [
                {
                    "strike_price": 25000,
                }
            ],
            "source": self.name,
            "source_confidence": 95,
            "data_status": "LIVE",
        }


class FakeStaleProvider(
    OptionChainProvider
):
    name = "FAKE_STALE"
    confidence = 60

    def fetch(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [
                {
                    "strike_price": 25000,
                }
            ],
            "source": self.name,
            "source_confidence": 60,
            "data_status": "STALE",
        }


class TestWriteThroughProvider(
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

    def test_live_payload_is_cached(
        self,
    ) -> None:
        provider = (
            WriteThroughOptionChainProvider(
                provider=FakeLiveProvider(),
                cache=self.cache,
                ttl_seconds=60,
            )
        )

        result = provider.fetch("nifty")

        self.assertTrue(
            result["write_through_cache"]
        )

        cached = self.cache.read(
            namespace="option_chain",
            key="nifty",
            allow_stale=True,
        )

        self.assertIsNotNone(cached)

        self.assertEqual(
            cached["symbol"],
            "NIFTY",
        )

        self.assertEqual(
            len(cached["records"]),
            1,
        )

    def test_non_live_payload_is_blocked(
        self,
    ) -> None:
        provider = (
            WriteThroughOptionChainProvider(
                provider=FakeStaleProvider(),
                cache=self.cache,
            )
        )

        with self.assertRaises(
            OptionChainProviderError
        ):
            provider.fetch("NIFTY")

    def test_negative_ttl_blocked(
        self,
    ) -> None:
        with self.assertRaises(
            OptionChainProviderError
        ):
            WriteThroughOptionChainProvider(
                provider=FakeLiveProvider(),
                cache=self.cache,
                ttl_seconds=-1,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
