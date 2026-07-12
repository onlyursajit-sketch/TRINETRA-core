from __future__ import annotations

import unittest

from src.providers.live.cache_provider import (
    CacheOptionChainProvider,
)
from src.providers.option_chain_manager import (
    OptionChainManager,
)
from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class SuccessfulLiveProvider(
    OptionChainProvider
):
    name = "LIVE_TEST"
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


class FailedLiveProvider(
    OptionChainProvider
):
    name = "LIVE_TEST"
    confidence = 95

    def fetch(self, symbol: str) -> dict:
        raise OptionChainProviderError(
            "Simulated live failure."
        )


class TestOptionChainFallback(
    unittest.TestCase
):
    def test_live_provider_has_priority(
        self,
    ) -> None:
        cache = CacheOptionChainProvider(
            {
                "records": [
                    {
                        "strike_price": 24950,
                    }
                ]
            }
        )

        manager = OptionChainManager(
            [
                SuccessfulLiveProvider(),
                cache,
            ]
        )

        result = manager.fetch("nifty")

        self.assertEqual(
            result["provider_used"],
            "LIVE_TEST",
        )

        self.assertFalse(
            result["fallback_used"]
        )

        self.assertEqual(
            result["data_status"],
            "LIVE",
        )

    def test_cache_fallback_used(
        self,
    ) -> None:
        cache = CacheOptionChainProvider(
            {
                "records": [
                    {
                        "strike_price": 25000,
                    }
                ]
            }
        )

        manager = OptionChainManager(
            [
                FailedLiveProvider(),
                cache,
            ]
        )

        result = manager.fetch("NIFTY")

        self.assertEqual(
            result["provider_used"],
            "CACHE",
        )

        self.assertTrue(
            result["fallback_used"]
        )

        self.assertEqual(
            result["data_status"],
            "STALE",
        )

        self.assertEqual(
            len(result["provider_errors"]),
            1,
        )

    def test_all_sources_fail(
        self,
    ) -> None:
        empty_cache = (
            CacheOptionChainProvider(
                {
                    "records": [],
                }
            )
        )

        manager = OptionChainManager(
            [
                FailedLiveProvider(),
                empty_cache,
            ]
        )

        result = manager.fetch("NIFTY")

        self.assertEqual(
            result["manager_status"],
            "FAILED",
        )

        self.assertEqual(
            result["data_status"],
            "NO_DATA",
        )

        self.assertEqual(
            len(result["provider_errors"]),
            2,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
