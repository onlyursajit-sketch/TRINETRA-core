from __future__ import annotations

from typing import Any

from src.cache.json_cache import JSONCache
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
    allow_stale: bool = True,
) -> OptionChainManager:
    """
    Create TRINETRA's default verified provider chain.

    Priority:
    1. NSE live collector
    2. Unified JSON cache
    3. NO_DATA from OptionChainManager
    """

    live_provider = NSELiveOptionChainProvider(
        collector=collector
    )

    cache_provider = JSONCacheOptionChainProvider(
        cache=cache,
        allow_stale=allow_stale,
    )

    return OptionChainManager(
        providers=[
            live_provider,
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
        allow_stale: bool = True,
    ) -> None:
        self.manager = (
            manager
            or create_default_option_chain_manager(
                cache=cache,
                collector=collector,
                allow_stale=allow_stale,
            )
        )

    def collect(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        return self.manager.fetch(symbol)
