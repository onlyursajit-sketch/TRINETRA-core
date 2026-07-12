from __future__ import annotations

from typing import Any

from src.cache.json_cache import (
    JSONCache,
    JSONCacheError,
)
from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class WriteThroughOptionChainProvider(
    OptionChainProvider
):
    """
    Wraps a live option-chain provider.

    On successful verified fetch:
    - returns live payload
    - writes payload to JSON cache

    Cache write failure does not destroy valid live data.
    """

    name = "WRITE_THROUGH"

    def __init__(
        self,
        provider: OptionChainProvider,
        cache: JSONCache | None = None,
        namespace: str = "option_chain",
        ttl_seconds: int = 300,
    ) -> None:
        if ttl_seconds < 0:
            raise OptionChainProviderError(
                "Cache TTL cannot be negative."
            )

        self.provider = provider
        self.cache = cache or JSONCache()
        self.namespace = namespace
        self.ttl_seconds = ttl_seconds

    def fetch(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        clean_symbol = self.clean_symbol(
            symbol
        )

        payload = self.provider.fetch(
            clean_symbol
        )

        payload = self.validate_payload(
            payload
        )

        data_status = str(
            payload.get(
                "data_status",
                "UNKNOWN",
            )
        ).upper()

        if data_status != "LIVE":
            raise OptionChainProviderError(
                "Write-through provider accepts LIVE data only."
            )

        origin_provider = getattr(
            self.provider,
            "name",
            self.provider.__class__.__name__,
        )

        result = {
            **payload,
            "symbol": clean_symbol,
            "provider_name": origin_provider,
            "cache_wrapper": self.name,
            "write_through_cache": False,
            "cache_write_error": None,
        }

        try:
            self.cache.write(
                self.namespace,
                clean_symbol.lower(),
                payload,
                ttl_seconds=self.ttl_seconds,
            )

            result[
                "write_through_cache"
            ] = True

        except JSONCacheError as exc:
            result[
                "cache_write_error"
            ] = str(exc)

        return result
