from __future__ import annotations

from typing import Any

from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class OptionChainManagerError(Exception):
    """Raised when all option-chain sources fail."""


class OptionChainManager:
    """
    TRINETRA option-chain source manager.

    Flow:
    Primary provider
        -> fallback provider
        -> NO_DATA
    """

    def __init__(
        self,
        providers: list[OptionChainProvider],
    ) -> None:
        self.providers = providers

    def fetch(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        errors: list[str] = []

        for provider in self.providers:
            try:
                result = provider.fetch(symbol)

                if not isinstance(result, dict):
                    raise OptionChainProviderError(
                        "Provider returned invalid payload."
                    )

                return {
                    **result,
                    "manager_status": "SUCCESS",
                    "provider_used": provider.name,
                    "fallback_used": bool(errors),
                    "provider_errors": errors,
                }

            except Exception as exc:
                errors.append(
                    f"{provider.name}: {exc}"
                )

        return {
            "symbol": symbol.strip().upper(),
            "records": [],
            "source": None,
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "manager_status": "FAILED",
            "provider_used": None,
            "fallback_used": False,
            "provider_errors": errors,
        }
