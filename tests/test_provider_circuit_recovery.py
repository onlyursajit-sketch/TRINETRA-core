from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from src.providers.option_chain_manager import OptionChainManager
from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class RecoveringProvider(OptionChainProvider):
    name = "RECOVERING"
    confidence = 90

    def __init__(self) -> None:
        self.calls = 0
        self.should_fail = True

    def fetch(self, symbol: str) -> dict:
        self.calls += 1

        if self.should_fail:
            raise OptionChainProviderError(
                "Simulated temporary failure."
            )

        return {
            "symbol": self.clean_symbol(symbol),
            "records": [{"strike_price": 25000}],
            "source": self.name,
            "source_confidence": 90,
            "data_status": "LIVE",
        }


class BackupProvider(OptionChainProvider):
    name = "BACKUP"
    confidence = 70

    def fetch(self, symbol: str) -> dict:
        return {
            "symbol": self.clean_symbol(symbol),
            "records": [{"strike_price": 25000}],
            "source": self.name,
            "source_confidence": 70,
            "data_status": "LIVE",
        }


class TestProviderCircuitRecovery(unittest.TestCase):
    def test_provider_recovers_after_cooldown(self) -> None:
        recovering = RecoveringProvider()

        manager = OptionChainManager(
            [recovering, BackupProvider()]
        )

        for _ in range(3):
            manager.fetch("NIFTY")

        health = manager.health[id(recovering)]

        self.assertFalse(health.is_available())

        health.circuit_open_until = (
            datetime.now(timezone.utc)
            - timedelta(seconds=1)
        )

        recovering.should_fail = False

        result = manager.fetch("NIFTY")

        self.assertEqual(
            result["provider_used"],
            "RECOVERING",
        )

        self.assertEqual(
            recovering.calls,
            4,
        )

        self.assertEqual(
            health.failure_count,
            0,
        )

        self.assertEqual(
            health.success_count,
            1,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
