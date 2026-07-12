from __future__ import annotations

from typing import Any

from src.providers.option_chain_provider import (
    OptionChainProvider,
)


class CacheOptionChainProvider(
    OptionChainProvider,
):
    """
    Cache fallback provider.

    Used only when
    live provider fails.
    """

    name = "CACHE"

    confidence = 60

    def __init__(
        self,
        payload: dict[str, Any] | None = None,
    ):
        self.payload = payload or {
            "records": []
        }

    def fetch(
        self,
        symbol: str,
    ) -> dict[str, Any]:

        payload = dict(self.payload)

        payload["symbol"] = (
            symbol.upper()
        )

        payload["source"] = self.name

        payload[
            "source_confidence"
        ] = self.confidence

        payload[
            "data_status"
        ] = "STALE"

        return payload
