from __future__ import annotations

import os

from typing import Any

from src.cache.json_cache import JSONCache
from src.providers.broker.broker_provider import (
    BrokerOptionChainProvider,
    DhanOptionChainProvider,
)
from src.providers.live.json_cache_provider import (
    JSONCacheOptionChainProvider,
)
from src.providers.live.nse_provider import (
    NSELiveOptionChainProvider,
)
from src.providers.option_chain_manager import (
    OptionChainManager,
)


def create_default_option_chain_manager(
    cache: JSONCache | None = None,
    collector: Any | None = None,
    broker_provider: Any | None = None,
    allow_stale: bool = True,
) -> OptionChainManager:
    """
    Create TRINETRA's default verified provider chain.

    Priority:
    1. NSE live collector
    2. Unified JSON cache
    3. NO_DATA from OptionChainManager
    """

    live_provider = WriteThroughOptionChainProvider(
    provider=NSELiveOptionChainProvider(
        collector=collector,
    ),
    cache=cache,
    ttl_seconds=300,
    )

    raw_broker_provider = broker_provider

    if raw_broker_provider is None:
        dhan_client_id = os.getenv("DHAN_CLIENT_ID")
        dhan_access_token = os.getenv("DHAN_ACCESS_TOKEN")
        dhan_expiry = os.getenv("DHAN_OPTION_EXPIRY")

        if dhan_client_id and dhan_access_token and dhan_expiry:
            raw_broker_provider = DhanOptionChainProvider(
                client_id=dhan_client_id,
                access_token=dhan_access_token,
                expiry=dhan_expiry,
            )
        else:
            raw_broker_provider = BrokerOptionChainProvider()

    broker = WriteThroughOptionChainProvider(
        provider=raw_broker_provider,
        cache=cache,
        ttl_seconds=300,
    )

    cache_provider = JSONCacheOptionChainProvider(
        cache=cache,
        allow_stale=allow_stale,
    )

    return OptionChainManager(
        providers=[
            live_provider,
            broker,
            cache_provider,
        ]
    )


class ManagedOptionChainCollector:
    """
    Collector-compatible adapter for OptionsAnalyticsPipeline.

    Exposes collect(symbol), while internally using
    the provider manager and fallback chain.
    """

    def __init__(
        self,
        manager: OptionChainManager | None = None,
        cache: JSONCache | None = None,
        collector: Any | None = None,
        broker_provider: Any | None = None,
        allow_stale: bool = True,
    ) -> None:
        self.manager = (
            manager
            or create_default_option_chain_manager(
                cache=cache,
                collector=collector,
                broker_provider=broker_provider,
                allow_stale=allow_stale,
            )
        )

    def collect(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        return self.manager.fetch(symbol)

from src.providers.live.write_through_provider import (
    WriteThroughOptionChainProvider,
)
