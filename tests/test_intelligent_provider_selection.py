import unittest

from src.providers.option_chain_manager import OptionChainManager
from src.providers.option_chain_provider import OptionChainProvider


class BadProvider(OptionChainProvider):
    name = "BAD"

    def fetch(self, symbol: str):
        raise RuntimeError("Provider failed")


class GoodProvider(OptionChainProvider):
    name = "GOOD"

    def fetch(self, symbol: str):
        return {
            "records": [{"strike": 100}],
            "provider_name": self.name,
        }


class TestIntelligentProviderSelection(unittest.TestCase):

    def test_manager_prefers_healthy_provider(self):
        manager = OptionChainManager(
            [BadProvider(), GoodProvider()]
        )

        manager.fetch("NIFTY")

        result = manager.fetch("NIFTY")

        self.assertEqual(
            result["provider_used"],
            "GOOD",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
