from __future__ import annotations

from typing import Any

from src.providers.option_chain_provider import (
    OptionChainProvider,
)


class BrokerOptionChainProvider(
    OptionChainProvider,
):
    """
    Placeholder for future broker APIs.

    Future:
    - Dhan
    - Zerodha
    - Angel
    """

    name = "BROKER"
    confidence = 90

    def fetch(
        self,
        symbol: str,
    ) -> dict[str, Any]:

        return {
            "symbol": self.clean_symbol(symbol),
            "records": [],
            "source": "BROKER",
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "fallback_reason": (
                "Broker API not configured."
            ),
        }
