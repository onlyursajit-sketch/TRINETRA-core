from __future__ import annotations

from typing import Any

from src.intelligence.market_context import MarketContext


class OptionChainContextAdapter:
    """Maps verified options analytics into MarketContext."""

    @staticmethod
    def _number(value: Any) -> float | None:
        if isinstance(value, bool):
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def apply(
        self,
        context: MarketContext,
        options_result: dict[str, Any],
    ) -> MarketContext:
        if not isinstance(options_result, dict):
            return context

        pcr_payload = options_result.get("pcr", {})
        max_pain_payload = options_result.get(
            "max_pain",
            {},
        )
        oi_payload = options_result.get("oi", {})

        if isinstance(pcr_payload, dict):
            context.pcr = self._number(
                pcr_payload.get("overall_pcr")
            )

        if isinstance(max_pain_payload, dict):
            max_pain = self._number(
                max_pain_payload.get(
                    "max_pain_strike"
                )
            )

            if max_pain is not None:
                context.max_pain = int(max_pain)

        if isinstance(oi_payload, dict):
            call_change = self._number(
                oi_payload.get(
                    "total_call_oi_change"
                )
            )
            put_change = self._number(
                oi_payload.get(
                    "total_put_oi_change"
                )
            )

            if (
                call_change is not None
                and put_change is not None
            ):
                context.oi_bullish = (
                    put_change > call_change
                )

            call_volume = self._number(
                oi_payload.get(
                    "total_call_volume"
                )
            )
            put_volume = self._number(
                oi_payload.get(
                    "total_put_volume"
                )
            )

            if (
                call_volume is not None
                and put_volume is not None
            ):
                context.volume_bullish = (
                    put_volume > call_volume
                )

        return context
