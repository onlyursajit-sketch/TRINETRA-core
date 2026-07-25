from __future__ import annotations

from typing import Any


class WhyEngine:
    """Build structured and backward-compatible decision explanations."""

    @staticmethod
    def _metadata(message: str) -> dict[str, str]:
        text = message.lower()

        category = "GENERAL"
        source = "DECISION_ENGINE"
        strength = "MODERATE"

        if "put-call ratio" in text or "pcr" in text:
            category = "PCR"
            source = "OPTION_CHAIN"
        elif "open interest" in text:
            category = "OPEN_INTEREST"
            source = "OPTION_CHAIN"
        elif "volume" in text:
            category = "VOLUME"
            source = "MARKET_DATA"
        elif "support" in text:
            category = "SUPPORT"
            source = "OPTION_CHAIN"
        elif "resistance" in text:
            category = "RESISTANCE"
            source = "OPTION_CHAIN"
        elif "confluence" in text:
            category = "CONFLUENCE"
            source = "MULTI_SIGNAL"
            strength = "STRONG"

        if "bullish" in text:
            bias = "BULLISH"
        elif "bearish" in text:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"

        return {
            "category": category,
            "bias": bias,
            "source": source,
            "strength": strength,
        }

    @classmethod
    def _items(cls, messages: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "sequence": index,
                "message": message,
                **cls._metadata(message),
            }
            for index, message in enumerate(messages, start=1)
        ]

    @classmethod
    def build(
        cls,
        *,
        decision: str,
        confidence_score: float,
        reasons: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "decision": decision,
            "confidence_score": confidence_score,
            "causes": cls._items(reasons),
            "warnings": cls._items(warnings),
        }
