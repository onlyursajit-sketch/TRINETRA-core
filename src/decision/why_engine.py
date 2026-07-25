from __future__ import annotations

from typing import Any


class WhyEngine:
    """Build structured causes, warnings, dominant drivers, and narrative."""

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

    @staticmethod
    def _build_narrative(
        *,
        decision: str,
        confidence_score: float,
        bullish: dict[str, Any] | None,
        bearish: dict[str, Any] | None,
        risk: dict[str, Any] | None,
    ) -> dict[str, str | None]:
        if decision == "BUY_BIAS" and bullish is not None:
            headline = (
                f"{decision} supported by bullish "
                f"{bullish['category']}."
            )
        elif decision == "SELL_BIAS" and bearish is not None:
            headline = (
                f"{decision} supported by bearish "
                f"{bearish['category']}."
            )
        elif decision == "WAIT":
            headline = (
                "WAIT until a dominant directional driver emerges."
            )
        elif decision == "NO_TRADE":
            headline = (
                "NO_TRADE because decision-quality requirements "
                "are not met."
            )
        else:
            headline = (
                f"{decision} has no dominant directional driver."
            )

        counter_signal = (
            f"Primary counter-signal: bearish {bearish['category']}."
            if decision == "BUY_BIAS" and bearish is not None
            else (
                f"Primary counter-signal: bullish {bullish['category']}."
                if decision == "SELL_BIAS" and bullish is not None
                else None
            )
        )

        risk_summary = (
            f"Primary risk: {risk['severity']} "
            f"{risk['category']} warning."
            if risk is not None
            else None
        )

        if confidence_score >= 80.0:
            confidence_level = "HIGH"
        elif confidence_score >= 60.0:
            confidence_level = "MODERATE"
        else:
            confidence_level = "LOW"

        return {
            "headline": headline,
            "counter_signal": counter_signal,
            "risk": risk_summary,
            "confidence_level": confidence_level,
            "confidence_statement": (
                f"Decision confidence is {confidence_level} "
                f"at {confidence_score:.1f}%."
            ),
        }

    @staticmethod
    def _normalise_messages(messages: Any) -> list[str]:
        if not isinstance(messages, (list, tuple)):
            return []

        return [
            message.strip()
            for message in messages
            if isinstance(message, str) and message.strip()
        ]

    @staticmethod
    def _normalise_confidence(value: Any) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.0

        if confidence != confidence:
            return 0.0

        if confidence in (float("inf"), float("-inf")):
            return 0.0

        return max(0.0, min(100.0, confidence))

    @staticmethod
    def validate_contract(payload: Any) -> list[str]:
        errors: list[str] = []

        if not isinstance(payload, dict):
            return ["payload must be a dictionary"]

        if payload.get("schema_version") != "1.0":
            errors.append("schema_version must be 1.0")

        decision = payload.get("decision")
        if not isinstance(decision, str) or not decision.strip():
            errors.append("decision must be a non-empty string")

        confidence_score = payload.get("confidence_score")
        if (
            not isinstance(confidence_score, (int, float))
            or isinstance(confidence_score, bool)
            or not 0.0 <= float(confidence_score) <= 100.0
        ):
            errors.append(
                "confidence_score must be between 0 and 100"
            )

        if not isinstance(payload.get("causes"), list):
            errors.append("causes must be a list")

        if not isinstance(payload.get("warnings"), list):
            errors.append("warnings must be a list")

        if not isinstance(payload.get("dominant_drivers"), dict):
            errors.append("dominant_drivers must be a dictionary")

        if not isinstance(payload.get("narrative"), dict):
            errors.append("narrative must be a dictionary")

        return errors

    @classmethod
    def build(
        cls,
        *,
        decision: str,
        confidence_score: float,
        reasons: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        decision = (
            decision.strip()
            if isinstance(decision, str) and decision.strip()
            else "WAIT"
        )

        confidence_score = cls._normalise_confidence(
            confidence_score
        )
        reasons = cls._normalise_messages(reasons)
        warnings = cls._normalise_messages(warnings)

        causes = cls._causes(reasons)
        structured_warnings = cls._warnings(warnings)

        bullish = cls._dominant_cause(causes, "BULLISH")
        bearish = cls._dominant_cause(causes, "BEARISH")
        risk = cls._dominant_warning(structured_warnings)

        payload = {
            "schema_version": "1.0",
            "decision": decision,
            "confidence_score": confidence_score,
            "causes": causes,
            "warnings": structured_warnings,
            "dominant_drivers": {
                "bullish": bullish,
                "bearish": bearish,
                "risk": risk,
            },
            "narrative": cls._build_narrative(
                decision=decision,
                confidence_score=confidence_score,
                bullish=bullish,
                bearish=bearish,
                risk=risk,
            ),
        }

        contract_errors = cls.validate_contract(payload)
        payload["contract_valid"] = not contract_errors
        payload["contract_errors"] = contract_errors

        return payload
