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


class JSONCacheOptionChainProvider(
    OptionChainProvider
):
    """
    Reads the latest verified option-chain payload
    from TRINETRA's unified JSON cache.

    It is a fallback provider, never a live source.
    """

    name = "JSON_CACHE"
    confidence = 60

    def __init__(
        self,
        cache: JSONCache | None = None,
        namespace: str = "option_chain",
        allow_stale: bool = True,
    ) -> None:
        self.cache = cache or JSONCache()
        self.namespace = namespace
        self.allow_stale = allow_stale

    def fetch(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        clean_symbol = self.clean_symbol(
            symbol
        )

        cache_key = clean_symbol.lower()

        try:
            payload = self.cache.read(
                namespace=self.namespace,
                key=cache_key,
                allow_stale=self.allow_stale,
            )

        except JSONCacheError as exc:
            raise OptionChainProviderError(
                f"JSON cache read failed: {exc}"
            ) from exc

        if payload is None:
            raise OptionChainProviderError(
                f"No cached option-chain data for {clean_symbol}."
            )

        records = payload.get("records")

        if not isinstance(records, list):
            raise OptionChainProviderError(
                "Cached option-chain records are invalid."
            )

        if not records:
            raise OptionChainProviderError(
                "Cached option-chain records are empty."
            )

        cache_info = payload.get(
            "cache_info",
            {},
        )

        is_stale = False

        if isinstance(cache_info, dict):
            is_stale = bool(
                cache_info.get("is_stale")
            )

        data_status = (
            "STALE"
            if is_stale
            else "LIVE"
        )

        cached_confidence = payload.get(
            "source_confidence",
            self.confidence,
        )

        try:
            cached_confidence_value = float(
                cached_confidence
            )
        except (TypeError, ValueError):
            cached_confidence_value = float(
                self.confidence
            )

        fallback_limit = (
            50.0
            if is_stale
            else 70.0
        )

        source_confidence = max(
            0.0,
            min(
                fallback_limit,
                cached_confidence_value,
            ),
        )

        return {
            **payload,
            "symbol": clean_symbol,
            "records": records,
            "source": self.name,
            "source_confidence": (
                source_confidence
            ),
            "data_status": data_status,
            "fallback_source": True,
        }
