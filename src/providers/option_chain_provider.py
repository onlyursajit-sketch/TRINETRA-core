from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class OptionChainProviderError(Exception):
    """Raised when an option-chain provider fails."""


class OptionChainProvider(ABC):
    """
    Base interface for verified option-chain providers.

    Future providers:
    - Broker API
    - Official exchange source
    - Cached snapshot
    """

    name = "BASE_PROVIDER"
    confidence = 0

    @abstractmethod
    def fetch(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        """Return normalized option-chain payload."""

    @staticmethod
    def clean_symbol(symbol: str) -> str:
        if not isinstance(symbol, str):
            raise OptionChainProviderError(
                "Symbol must be a string."
            )

        cleaned = symbol.strip().upper()

        if not cleaned:
            raise OptionChainProviderError(
                "Symbol cannot be empty."
            )

        return cleaned

    @staticmethod
    def validate_payload(
        payload: Any,
    ) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise OptionChainProviderError(
                "Provider payload must be a dictionary."
            )

        records = payload.get("records")

        if not isinstance(records, list):
            raise OptionChainProviderError(
                "Provider payload requires records list."
            )

        return payload


class FixtureOptionChainProvider(
    OptionChainProvider
):
    """
    Development provider for tests only.

    Never treated as live market data.
    """

    name = "FIXTURE"
    confidence = 0

    def __init__(
        self,
        payload: dict[str, Any],
    ) -> None:
        self.payload = payload

    def fetch(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        clean_symbol = self.clean_symbol(
            symbol
        )

        payload = self.validate_payload(
            self.payload
        )

        return {
            **payload,
            "symbol": clean_symbol,
            "source": self.name,
            "source_confidence": self.confidence,
            "data_status": "TEST_FIXTURE",
        }
