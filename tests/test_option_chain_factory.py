from __future__ import annotations

import tempfile
import unittest

from src.cache.json_cache import JSONCache
from src.providers.option_chain_factory import (
    ManagedOptionChainCollector,
    create_default_option_chain_manager,
)


class FakeLiveCollectorSuccess:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [
                {
                    "strike_price": 25000,
                    "expiry_date": "17-Jul-2026",
                    "ce": {
                        "openInterest": 1000,
                    },
                    "pe": {
                        "openInterest": 1200,
                    },
                }
            ],
            "nearest_expiry": "17-Jul-2026",
            "underlying_value": 25010,
            "atm_strike": 25000,
            "source": "NSE",
            "source_confidence": 95,
            "data_status": "LIVE",
        }


class FakeLiveCollectorFailure:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [],
            "source": "NSE",
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "fallback_reason": "Simulated live failure.",
        }


class TestOptionChainFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_live_provider_has_priority(self) -> None:
        manager = create_default_option_chain_manager(
            cache=self.cache,
            collector=FakeLiveCollectorSuccess(),
        )

        result = manager.fetch("nifty")

        self.assertEqual(
            result["provider_used"],
            "NSE",
        )

        self.assertFalse(
            result["fallback_used"]
        )

        self.assertEqual(
            result["data_status"],
            "LIVE",
        )

    def test_json_cache_fallback(self) -> None:
        self.cache.write(
            "option_chain",
            "nifty",
            {
                "symbol": "NIFTY",
                "records": [
                    {
                        "strike_price": 25000,
                        "expiry_date": "17-Jul-2026",
                        "ce": {
                            "openInterest": 1000,
                        },
                        "pe": {
                            "openInterest": 1200,
                        },
                    }
                ],
                "nearest_expiry": "17-Jul-2026",
                "underlying_value": 25010,
                "atm_strike": 25000,
                "source_confidence": 95,
                "data_status": "LIVE",
            },
            ttl_seconds=60,
        )

        collector = ManagedOptionChainCollector(
            cache=self.cache,
            collector=FakeLiveCollectorFailure(),
        )

        result = collector.collect("NIFTY")

        self.assertEqual(
            result["provider_used"],
            "JSON_CACHE",
        )

        self.assertTrue(
            result["fallback_used"]
        )

        self.assertEqual(
            result["data_status"],
            "LIVE",
        )

    def test_all_sources_fail(self) -> None:
        collector = ManagedOptionChainCollector(
            cache=self.cache,
            collector=FakeLiveCollectorFailure(),
        )

        result = collector.collect("NIFTY")

        self.assertEqual(
            result["manager_status"],
            "FAILED",
        )

        self.assertEqual(
            result["data_status"],
            "NO_DATA",
        )

        self.assertEqual(
            result["records"],
            [],
        )

        self.assertEqual(
            len(result["provider_errors"]),
            3,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)


def test_factory_uses_configured_dhan_provider() -> None:
    from src.providers.broker.broker_provider import DhanOptionChainProvider
    from src.providers.live.write_through_provider import (
        WriteThroughOptionChainProvider,
    )

    dhan = DhanOptionChainProvider(
        client_id="demo-client",
        access_token="demo-token",
        expiry="2026-07-16",
    )

    manager = create_default_option_chain_manager(
        cache=JSONCache(base_dir=tempfile.mkdtemp()),
        collector=FakeLiveCollectorFailure(),
        broker_provider=dhan,
    )

    assert len(manager.providers) == 3

    broker_wrapper = manager.providers[1]
    assert isinstance(
        broker_wrapper,
        WriteThroughOptionChainProvider,
    )
    assert broker_wrapper.provider is dhan


def test_factory_auto_configures_dhan_from_environment() -> None:
    from unittest.mock import patch

    from src.providers.broker.broker_provider import DhanOptionChainProvider
    from src.providers.live.write_through_provider import (
        WriteThroughOptionChainProvider,
    )

    with patch.dict(
        "os.environ",
        {
            "DHAN_CLIENT_ID": "demo-client",
            "DHAN_ACCESS_TOKEN": "demo-token",
            "DHAN_OPTION_EXPIRY": "2026-07-16",
        },
        clear=False,
    ):
        manager = create_default_option_chain_manager(
            cache=JSONCache(base_dir=tempfile.mkdtemp()),
            collector=FakeLiveCollectorFailure(),
        )

    broker_wrapper = manager.providers[1]

    assert isinstance(
        broker_wrapper,
        WriteThroughOptionChainProvider,
    )
    assert isinstance(
        broker_wrapper.provider,
        DhanOptionChainProvider,
    )
    assert broker_wrapper.provider.expiry == "2026-07-16"


def test_factory_uses_placeholder_broker_without_dhan_environment() -> None:
    from unittest.mock import patch

    from src.providers.broker.broker_provider import BrokerOptionChainProvider
    from src.providers.live.write_through_provider import (
        WriteThroughOptionChainProvider,
    )

    with patch.dict(
        "os.environ",
        {
            "DHAN_CLIENT_ID": "",
            "DHAN_ACCESS_TOKEN": "",
            "DHAN_OPTION_EXPIRY": "",
        },
        clear=False,
    ):
        manager = create_default_option_chain_manager(
            cache=JSONCache(base_dir=tempfile.mkdtemp()),
            collector=FakeLiveCollectorFailure(),
        )

    broker_wrapper = manager.providers[1]

    assert isinstance(
        broker_wrapper,
        WriteThroughOptionChainProvider,
    )
    assert isinstance(
        broker_wrapper.provider,
        BrokerOptionChainProvider,
    )


def test_factory_uses_dhan_without_explicit_expiry(monkeypatch) -> None:
    from src.providers.option_chain_factory import (
        create_default_option_chain_manager,
    )

    monkeypatch.setenv("DHAN_CLIENT_ID", "test-client")
    monkeypatch.setenv("DHAN_ACCESS_TOKEN", "test-token")
    monkeypatch.delenv("DHAN_OPTION_EXPIRY", raising=False)

    manager = create_default_option_chain_manager()

    provider_names = [
        getattr(
            getattr(provider, "provider", None),
            "name",
            provider.name,
        )
        for provider in manager.providers
    ]

    assert "DHAN" in provider_names
    assert "BROKER" not in provider_names
