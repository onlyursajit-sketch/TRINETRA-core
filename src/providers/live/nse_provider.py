from __future__ import annotations

from typing import Any

from src.collectors.nse_option_chain import (
    NSEOptionChainCollector,
)
from src.providers.option_chain_provider import (
    OptionChainProvider,
    OptionChainProviderError,
)


class NSELiveOptionChainProvider(
    OptionChainProvider
):
    """
    Adapter between the existing NSE collector
    and the TRINETRA provider-manager interface.

    The provider never fabricates option-chain data.
    """

    name = "NSE"
    confidence = 95

    def __init__(
        self,
        collector: Any | None = None,
    ) -> None:
        self.collector = (
            collector
            or NSEOptionChainCollector()
        )

    @staticmethod
    def _extract_records(
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        records = payload.get("records")

        if isinstance(records, list):
            return records

        option_chain = payload.get(
            "option_chain"
        )

        if isinstance(option_chain, list):
            return option_chain

        data = payload.get("data")

        if isinstance(data, list):
            return data

        return []

    def fetch(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        clean_symbol = self.clean_symbol(
            symbol
        )

        try:
            payload = self.collector.collect(
                clean_symbol
            )

        except Exception as exc:
            raise OptionChainProviderError(
                f"NSE collector failed: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise OptionChainProviderError(
                "NSE collector returned invalid payload."
            )

        data_status = str(
            payload.get(
                "data_status",
                "UNKNOWN",
            )
        ).upper()

        records = self._extract_records(
            payload
        )

        if data_status == "NO_DATA":
            fallback_reason = payload.get(
                "fallback_reason",
                "NSE data unavailable.",
            )

            raise OptionChainProviderError(
                str(fallback_reason)
            )

        if not records:
            raise OptionChainProviderError(
                "NSE payload contains no option-chain records."
            )

        source_confidence = payload.get(
            "source_confidence",
            self.confidence,
        )

        try:
            confidence = float(
                source_confidence
            )
        except (TypeError, ValueError):
            confidence = float(
                self.confidence
            )

        confidence = max(
            0.0,
            min(
                100.0,
                confidence,
            ),
        )

        return {
            **payload,
            "symbol": clean_symbol,
            "records": records,
            "source": payload.get(
                "source",
                self.name,
            ),
            "source_confidence": confidence,
            "data_status": data_status,
        }
