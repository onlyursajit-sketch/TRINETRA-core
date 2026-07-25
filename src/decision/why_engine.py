from __future__ import annotations

from typing import Any


class WhyEngine:
    """Build structured decision causes, warnings, and dominant drivers."""

    _STRENGTH_RANK = {
        "WEAK": 1,
        "MODERATE": 2,
        "STRONG": 3,
    }

    _SEVERITY_RANK = {
        "LOW": 1,
        "MODERATE": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }

    @staticmethod
    def _cause_metadata(message: str) -> dict[str, str]:
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

    @staticmethod
    def _warning_metadata(message: str) -> dict[str, str]:
        text = message.lower()

        category = "GENERAL_WARNING"
        source = "DECISION_ENGINE"
        severity = "MODERATE"

        if "vix" in text:
            category = "VOLATILITY"
            source = "INDIA_VIX"
            severity = "CRITICAL" if "extremely" in text else "HIGH"
        elif "source confidence" in text:
            category = "DATA_QUALITY"
            source = "SOURCE_CONFIDENCE"
            severity = "HIGH"
        elif "stale" in text:
            category = "DATA_FRESHNESS"
            source = "MARKET_DATA"
            severity = "HIGH"
        elif "no data" in text or "unavailable" in text:
            category = "DATA_AVAILABILITY"
            source = "MARKET_DATA"
            severity = "CRITICAL"

        return {
            "category": category,
            "source": source,
            "severity": severity,
        }

    @classmethod
    def _causes(cls, messages: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "sequence": index,
                "message": message,
                **cls._cause_metadata(message),
            }
            for index, message in enumerate(messages, start=1)
        ]

    @classmethod
    def _warnings(cls, messages: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "sequence": index,
                "message": message,
                **cls._warning_metadata(message),
            }
            for index, message in enumerate(messages, start=1)
        ]

    @classmethod
    def _dominant_cause(
        cls,
        causes: list[dict[str, Any]],
        bias: str,
    ) -> dict[str, Any] | None:
        matching = [
            cause
            for cause in causes
            if cause.get("bias") == bias
        ]

        if not matching:
            return None

        return max(
            matching,
            key=lambda cause: cls._STRENGTH_RANK.get(
                str(cause.get("strength")),
                0,
            ),
        )

    @classmethod
    def _dominant_warning(
        cls,
        warnings: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not warnings:
            return None

        return max(
            warnings,
            key=lambda warning: cls._SEVERITY_RANK.get(
                str(warning.get("severity")),
                0,
            ),
        )

    @classmethod
    def build(
        cls,
        *,
        decision: str,
        confidence_score: float,
        reasons: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        causes = cls._causes(reasons)
        structured_warnings = cls._warnings(warnings)

        return {
            "schema_version": "1.0",
            "decision": decision,
            "confidence_score": confidence_score,
            "causes": causes,
            "warnings": structured_warnings,
            "dominant_drivers": {
                "bullish": cls._dominant_cause(causes, "BULLISH"),
                "bearish": cls._dominant_cause(causes, "BEARISH"),
                "risk": cls._dominant_warning(structured_warnings),
            },
        }
