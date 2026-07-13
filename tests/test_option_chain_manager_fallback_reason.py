from __future__ import annotations

import unittest

from src.providers.option_chain_manager import OptionChainManager


class FailingProvider:
    name = "FAIL_PROVIDER"

    def fetch(self, symbol: str) -> dict:
        raise RuntimeError(f"failed for {symbol}")


class TestOptionChainManagerFallbackReason(unittest.TestCase):
    def test_no_data_contains_fallback_reason(self) -> None:
        manager = OptionChainManager(
            providers=[FailingProvider()],
        )

        result = manager.fetch("NIFTY")

        self.assertEqual(result["data_status"], "NO_DATA")
        self.assertIsNone(result["source"])
        self.assertIn(
            "FAIL_PROVIDER: failed for NIFTY",
            result["fallback_reason"],
        )
        self.assertEqual(
            result["provider_errors"],
            ["FAIL_PROVIDER: failed for NIFTY"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
