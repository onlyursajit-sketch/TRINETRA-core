import unittest

from src.providers.live.cache_provider import (
    CacheOptionChainProvider,
)


class TestCacheProvider(
    unittest.TestCase
):

    def test_cache_provider(self):

        provider = CacheOptionChainProvider(
            {
                "records":[
                    {
                        "strike_price":25000
                    }
                ]
            }
        )

        result = provider.fetch(
            "nifty"
        )

        self.assertEqual(
            result["source"],
            "CACHE",
        )

        self.assertEqual(
            result["data_status"],
            "STALE",
        )


if __name__=="__main__":
    unittest.main()
