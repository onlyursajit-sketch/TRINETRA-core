import unittest

from src.providers.option_chain_manager import (
    OptionChainManager,
)
from src.providers.option_chain_provider import (
    FixtureOptionChainProvider,
)


class TestOptionChainManager(unittest.TestCase):

    def test_primary_provider_success(self):
        provider = FixtureOptionChainProvider(
            {
                "records": [
                    {"strike_price": 25000}
                ]
            }
        )

        manager = OptionChainManager(
            [provider]
        )

        result = manager.fetch("nifty")

        self.assertEqual(
            result["manager_status"],
            "SUCCESS",
        )

        self.assertEqual(
            result["provider_used"],
            "FIXTURE",
        )

    def test_all_providers_fail(self):
        bad_provider = FixtureOptionChainProvider(
            {
                "records": None
            }
        )

        manager = OptionChainManager(
            [bad_provider]
        )

        result = manager.fetch("NIFTY")

        self.assertEqual(
            result["data_status"],
            "NO_DATA",
        )

        self.assertEqual(
            result["manager_status"],
            "FAILED",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
