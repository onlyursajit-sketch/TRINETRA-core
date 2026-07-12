from __future__ import annotations

from typing import Any

from src.providers.provider_health import ProviderHealth
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

        self.health = {
            id(provider): ProviderHealth()
            for provider in self.providers
        }

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

            provider_health = self.health[id(provider)]

            if not provider_health.is_available():
                errors.append(
                    f"{provider_name}: CIRCUIT_OPEN"
                )
                continue

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

                resolved_provider_name = (
                    result.get("provider_name")
                    or provider_name
                )

                provider_health.record_success()

                return {
                    **result,
                    "manager_status": "SUCCESS",
                    "provider_used": resolved_provider_name,
                    "fallback_used": index > 0,
                    "provider_errors": errors,
                }

            except Exception as exc:
                provider_health.record_failure(exc)

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

    def provider_health_report(self) -> dict:
        """Return provider health status."""

        report = {}

        for provider in self.providers:
            health = self.health[id(provider)]

            report[provider.name] = {
                "success_count": health.success_count,
                "failure_count": health.failure_count,
                "success_rate": health.success_rate,
                "available": health.is_available(),
                "circuit_open_until": (
                    health.circuit_open_until.isoformat()
                    if health.circuit_open_until
                    else None
                ),
            }

        return report


    def manager_health_summary(self) -> dict:
        report = self.provider_health_report()

        providers_total = len(report)
        providers_available = sum(
            1
            for item in report.values()
            if item["available"]
        )
        providers_unavailable = (
            providers_total - providers_available
        )

        total_attempts = sum(
            self.health[id(provider)].total_attempts
            for provider in self.providers
        )

        total_successes = sum(
            self.health[id(provider)].total_successes
            for provider in self.providers
        )

        overall_success_rate = (
            round(
                (
                    total_successes
                    / total_attempts
                )
                * 100.0,
                2,
            )
            if total_attempts
            else 0.0
        )

        status = (
            "HEALTHY"
            if providers_available == providers_total
            else "DEGRADED"
            if providers_available > 0
            else "UNAVAILABLE"
        )

        return {
            "status": status,
            "providers_total": providers_total,
            "providers_available": providers_available,
            "providers_unavailable": providers_unavailable,
            "overall_success_rate": overall_success_rate,
        }

