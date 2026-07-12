from __future__ import annotations

from typing import Any

from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class OptionChainManagerError(Exception):
    """Raised when option-chain manager input is invalid."""


class OptionChainManager:
    """
    Provider priority chain:

    Primary live provider
        -> cache provider
        -> NO_DATA
    """

    def __init__(
        self,
        providers: list[OptionChainProvider],
    ) -> None:
        if not isinstance(providers, list):
            raise OptionChainManagerError(
                "Providers must be supplied as a list."
            )

        self.providers = providers

    def fetch(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        if not isinstance(symbol, str):
            raise OptionChainManagerError(
                "Symbol must be a string."
            )

        clean_symbol = symbol.strip().upper()

        if not clean_symbol:
            raise OptionChainManagerError(
                "Symbol cannot be empty."
            )

        errors: list[str] = []

        for index, provider in enumerate(
            self.providers
        ):
            provider_name = getattr(
                provider,
                "name",
                provider.__class__.__name__,
            )

            try:
                result = provider.fetch(
                    clean_symbol
                )

                if not isinstance(result, dict):
                    raise OptionChainProviderError(
                        "Provider returned invalid payload."
                    )

                records = result.get("records")

                if not isinstance(records, list):
                    raise OptionChainProviderError(
                        "Provider records must be a list."
                    )

                if not records:
                    raise OptionChainProviderError(
                        "Provider returned empty records."
                    )

                return {
                    **result,
                    "manager_status": "SUCCESS",
                    "provider_used": provider_name,
                    "fallback_used": index > 0,
                    "provider_errors": errors,
                }

            except Exception as exc:
                errors.append(
                    f"{provider_name}: {exc}"
                )

        return {
            "symbol": clean_symbol,
            "records": [],
            "source": None,
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "manager_status": "FAILED",
            "provider_used": None,
            "fallback_used": False,
            "provider_errors": errors,
        }
