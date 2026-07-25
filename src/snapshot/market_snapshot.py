from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.cache.json_cache import JSONCache, JSONCacheError


class MarketSnapshotError(Exception):
    """Raised when unified market snapshot creation fails."""


class MarketSnapshotEngine:
    """
    TRINETRA Unified Market Snapshot Engine.

    Combines:
    - Options analytics
    - India VIX intelligence
    - FII/DII intelligence
    - Source confidence
    - LIVE / STALE / NO_DATA status
    - Institutional score
    - Deterministic market bias
    - Warning generation

    No fabricated values are generated.
    """

    VALID_DATA_STATUSES = {
        "LIVE",
        "STALE",
        "PARTIAL",
        "NO_DATA",
        "UNKNOWN",
    }

    SCORE_MIN = -100
    SCORE_MAX = 100

    def __init__(
        self,
        cache: JSONCache | None = None,
        snapshot_ttl_seconds: int = 300,
    ) -> None:
        if snapshot_ttl_seconds < 0:
            raise MarketSnapshotError(
                "Snapshot TTL cannot be negative."
            )

        self.cache = cache or JSONCache()
        self.snapshot_ttl_seconds = snapshot_ttl_seconds

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _number(
        value: Any,
        default: float | None = None,
    ) -> float | None:
        if isinstance(value, bool):
            return default

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clean_symbol(value: Any) -> str:
        if not isinstance(value, str):
            return "UNKNOWN"

        cleaned = value.strip().upper()

        return cleaned or "UNKNOWN"

    @classmethod
    def _normalize_status(
        cls,
        value: Any,
    ) -> str:
        if not isinstance(value, str):
            return "UNKNOWN"

        status = value.strip().upper()

        if status not in cls.VALID_DATA_STATUSES:
            return "UNKNOWN"

        return status

    @staticmethod
    def _require_dictionary(
        payload: Any,
        name: str,
    ) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise MarketSnapshotError(
                f"{name} payload must be a dictionary."
            )

        return payload

    @staticmethod
    def _add_warning(
        warnings: list[str],
        warning: str,
    ) -> None:
        if warning not in warnings:
            warnings.append(warning)

    @staticmethod
    def _clamp_score(score: float) -> float:
        return max(
            MarketSnapshotEngine.SCORE_MIN,
            min(
                MarketSnapshotEngine.SCORE_MAX,
                score,
            ),
        )

    @staticmethod
    def _confidence_label(
        statuses: list[str],
    ) -> str:
        if not statuses:
            return "NONE"

        no_data_count = statuses.count("NO_DATA")
        stale_count = statuses.count("STALE")
        partial_count = statuses.count("PARTIAL")
        unknown_count = statuses.count("UNKNOWN")

        if no_data_count >= 2:
            return "NONE"

        if no_data_count == 1:
            return "LOW"

        if stale_count >= 2:
            return "LOW"

        if (
            stale_count == 1
            or partial_count >= 1
            or unknown_count >= 1
        ):
            return "MEDIUM"

        if all(
            status == "LIVE"
            for status in statuses
        ):
            return "HIGH"

        return "MEDIUM"

    @staticmethod
    def _overall_data_status(
        statuses: list[str],
    ) -> str:
        if not statuses:
            return "NO_DATA"

        no_data_count = statuses.count("NO_DATA")
        stale_count = statuses.count("STALE")
        partial_count = statuses.count("PARTIAL")
        unknown_count = statuses.count("UNKNOWN")

        if no_data_count == len(statuses):
            return "NO_DATA"

        if (
            no_data_count > 0
            or partial_count > 0
            or unknown_count > 0
        ):
            return "PARTIAL"

        if stale_count > 0:
            return "STALE"

        if all(
            status == "LIVE"
            for status in statuses
        ):
            return "LIVE"

        return "PARTIAL"

    @staticmethod
    def _average_source_confidence(
        confidence_values: list[float | None],
    ) -> float:
        valid_values = [
            value
            for value in confidence_values
            if value is not None
            and 0 <= value <= 100
        ]

        if not valid_values:
            return 0.0

        return round(
            sum(valid_values) / len(valid_values),
            2,
        )
    def _extract_options_sections(
        self,
        options_payload: dict[str, Any],
    ) -> dict[str, Any]:
        options_payload = self._require_dictionary(
            options_payload,
            "Options analytics",
        )

        option_chain = options_payload.get("option_chain")
        oi = options_payload.get("oi")
        pcr = options_payload.get("pcr")
        max_pain = options_payload.get("max_pain")

        return {
            "symbol": self._clean_symbol(
                options_payload.get("symbol")
            ),
            "data_status": self._normalize_status(
                options_payload.get("data_status")
            ),
            "analytics_allowed": bool(
                options_payload.get(
                    "analytics_allowed",
                    False,
                )
            ),
            "option_chain": (
                option_chain
                if isinstance(option_chain, dict)
                else None
            ),
            "oi": (
                oi
                if isinstance(oi, dict)
                else None
            ),
            "pcr": (
                pcr
                if isinstance(pcr, dict)
                else None
            ),
            "max_pain": (
                max_pain
                if isinstance(max_pain, dict)
                else None
            ),
            "errors": (
                options_payload.get("errors")
                if isinstance(
                    options_payload.get("errors"),
                    list,
                )
                else []
            ),
        }

    def _collect_statuses(
        self,
        options_section: dict[str, Any],
        india_vix: dict[str, Any],
        fii_dii: dict[str, Any],
    ) -> list[str]:
        return [
            self._normalize_status(
                options_section.get("data_status")
            ),
            self._normalize_status(
                india_vix.get("data_status")
            ),
            self._normalize_status(
                fii_dii.get("data_status")
            ),
        ]

    def _collect_source_confidences(
        self,
        options_section: dict[str, Any],
        india_vix: dict[str, Any],
        fii_dii: dict[str, Any],
    ) -> list[float | None]:
        option_chain = options_section.get(
            "option_chain"
        )

        option_confidence = None

        if isinstance(option_chain, dict):
            option_confidence = self._number(
                option_chain.get(
                    "source_confidence"
                )
            )

        return [
            option_confidence,
            self._number(
                india_vix.get(
                    "source_confidence"
                )
            ),
            self._number(
                fii_dii.get(
                    "source_confidence"
                )
            ),
        ]

    def _generate_warnings(
        self,
        options_section: dict[str, Any],
        india_vix: dict[str, Any],
        fii_dii: dict[str, Any],
        overall_status: str,
        source_confidence: float,
    ) -> list[str]:
        warnings: list[str] = []

        options_status = self._normalize_status(
            options_section.get("data_status")
        )
        vix_status = self._normalize_status(
            india_vix.get("data_status")
        )
        flow_status = self._normalize_status(
            fii_dii.get("data_status")
        )

        if overall_status == "NO_DATA":
            self._add_warning(
                warnings,
                "NO_DATA",
            )

        if overall_status == "PARTIAL":
            self._add_warning(
                warnings,
                "PARTIAL_DATA",
            )

        if "STALE" in {
            options_status,
            vix_status,
            flow_status,
        }:
            self._add_warning(
                warnings,
                "STALE_DATA",
            )

        if options_status == "NO_DATA":
            self._add_warning(
                warnings,
                "OPTIONS_DATA_UNAVAILABLE",
            )

        if vix_status == "NO_DATA":
            self._add_warning(
                warnings,
                "INDIA_VIX_UNAVAILABLE",
            )

        if flow_status == "NO_DATA":
            self._add_warning(
                warnings,
                "FII_DII_DATA_UNAVAILABLE",
            )

        if not options_section.get(
            "analytics_allowed",
            False,
        ):
            self._add_warning(
                warnings,
                "OPTIONS_ANALYTICS_BLOCKED",
            )

        pcr = options_section.get("pcr")

        if isinstance(pcr, dict):
            overall_pcr = self._number(
                pcr.get("overall_pcr")
            )

            if overall_pcr is not None:
                if overall_pcr < 0.80:
                    self._add_warning(
                        warnings,
                        "LOW_PCR",
                    )

                if overall_pcr > 1.20:
                    self._add_warning(
                        warnings,
                        "HIGH_PCR",
                    )

        risk_regime = str(
            india_vix.get(
                "risk_regime",
                "",
            )
        ).upper()

        if risk_regime == "HIGH":
            self._add_warning(
                warnings,
                "HIGH_VIX",
            )

        if risk_regime == "EXTREME":
            self._add_warning(
                warnings,
                "EXTREME_VIX",
            )

        fii_section = fii_dii.get("fii")

        if isinstance(fii_section, dict):
            fii_cash_net = self._number(
                fii_section.get("cash_net")
            )

            if (
                fii_cash_net is not None
                and fii_cash_net < 0
            ):
                self._add_warning(
                    warnings,
                    "FII_SELLING",
                )

        if source_confidence < 60:
            self._add_warning(
                warnings,
                "LOW_SOURCE_CONFIDENCE",
            )

        for error in options_section.get(
            "errors",
            [],
        ):
            if isinstance(error, str) and error.strip():
                self._add_warning(
                    warnings,
                    f"OPTIONS_ERROR: {error.strip()}",
                )

        return warnings

    @staticmethod
    def _bias_from_score(
        score: float,
    ) -> str:
        if score >= 70:
            return "STRONG_BULLISH"
        if score >= 35:
            return "BULLISH"
        if score >= 15:
            return "MILD_BULLISH"
        if score > -15:
            return "NEUTRAL"
        if score > -35:
            return "MILD_BEARISH"
        if score > -70:
            return "BEARISH"
        return "STRONG_BEARISH"

    def _score_pcr(
        self,
        pcr_payload: dict[str, Any] | None,
    ) -> tuple[float, str]:
        if not isinstance(pcr_payload, dict):
            return 0.0, "PCR unavailable."

        overall_pcr = self._number(
            pcr_payload.get("overall_pcr")
        )

        if overall_pcr is None:
            return 0.0, "PCR unavailable."

        if overall_pcr < 0.60:
            return (
                -20.0,
                "PCR below 0.60 indicates extreme bearish positioning.",
            )

        if overall_pcr < 0.80:
            return (
                -15.0,
                "PCR below 0.80 indicates bearish positioning.",
            )

        if overall_pcr < 1.00:
            return (
                -5.0,
                "PCR below 1.00 indicates neutral-bearish positioning.",
            )

        if overall_pcr <= 1.20:
            return (
                15.0,
                "PCR between 1.00 and 1.20 supports bullish positioning.",
            )

        if overall_pcr <= 1.50:
            return (
                8.0,
                "PCR above 1.20 is bullish but may be crowded.",
            )

        return (
            0.0,
            "Very high PCR indicates crowded positioning and reversal risk.",
        )

    def _score_oi(
        self,
        oi_payload: dict[str, Any] | None,
    ) -> tuple[float, str]:
        if not isinstance(oi_payload, dict):
            return 0.0, "OI analytics unavailable."

        call_change = self._number(
            oi_payload.get("total_call_oi_change"),
            0.0,
        )
        put_change = self._number(
            oi_payload.get("total_put_oi_change"),
            0.0,
        )

        assert call_change is not None
        assert put_change is not None

        difference = put_change - call_change

        if difference >= 1000:
            return (
                25.0,
                "Put OI addition is substantially stronger than Call OI addition.",
            )

        if difference >= 250:
            return (
                15.0,
                "Put OI addition is stronger than Call OI addition.",
            )

        if difference > 0:
            return (
                8.0,
                "Put OI addition is moderately stronger.",
            )

        if difference <= -1000:
            return (
                -25.0,
                "Call OI addition is substantially stronger than Put OI addition.",
            )

        if difference <= -250:
            return (
                -15.0,
                "Call OI addition is stronger than Put OI addition.",
            )

        if difference < 0:
            return (
                -8.0,
                "Call OI addition is moderately stronger.",
            )

        return (
            0.0,
            "Call and Put OI additions are balanced.",
        )

    def _score_max_pain(
        self,
        max_pain_payload: dict[str, Any] | None,
    ) -> tuple[float, str]:
        if not isinstance(max_pain_payload, dict):
            return 0.0, "Max Pain unavailable."

        underlying = self._number(
            max_pain_payload.get("underlying_value")
        )
        max_pain = self._number(
            max_pain_payload.get("max_pain_strike")
        )

        if (
            underlying is None
            or max_pain is None
            or underlying <= 0
        ):
            return 0.0, "Max Pain comparison unavailable."

        difference = underlying - max_pain
        percentage_distance = (
            difference / underlying
        ) * 100

        if percentage_distance >= 0.75:
            return (
                20.0,
                "Underlying is materially above Max Pain.",
            )

        if percentage_distance >= 0.20:
            return (
                10.0,
                "Underlying is above Max Pain.",
            )

        if percentage_distance <= -0.75:
            return (
                -20.0,
                "Underlying is materially below Max Pain.",
            )

        if percentage_distance <= -0.20:
            return (
                -10.0,
                "Underlying is below Max Pain.",
            )

        return (
            0.0,
            "Underlying is close to Max Pain.",
        )

    def _score_vix(
        self,
        india_vix: dict[str, Any],
    ) -> tuple[float, str]:
        risk_regime = str(
            india_vix.get("risk_regime", "")
        ).upper()

        direction = str(
            india_vix.get("direction", "")
        ).upper()

        if risk_regime == "VERY_LOW":
            score = 12.0
            explanation = (
                "India VIX is in a very-low volatility regime."
            )
        elif risk_regime == "LOW":
            score = 15.0
            explanation = (
                "India VIX indicates a relatively stable environment."
            )
        elif risk_regime == "MODERATE":
            score = 5.0
            explanation = (
                "India VIX indicates moderate market risk."
            )
        elif risk_regime == "HIGH":
            score = -15.0
            explanation = (
                "India VIX indicates elevated market risk."
            )
        elif risk_regime == "EXTREME":
            score = -25.0
            explanation = (
                "India VIX indicates extreme market stress."
            )
        else:
            return 0.0, "India VIX regime unavailable."

        if direction == "UP":
            score -= 5.0
            explanation += " Volatility is rising."
        elif direction == "DOWN":
            score += 5.0
            explanation += " Volatility is declining."

        return score, explanation

    def _score_institutional_flows(
        self,
        fii_dii: dict[str, Any],
    ) -> tuple[float, str]:
        market_bias = str(
            fii_dii.get("market_bias", "")
        ).upper()

        if market_bias == "BULLISH":
            return (
                20.0,
                "FII and DII institutional flows are jointly bullish.",
            )

        if market_bias == "FII_BUYING_DOMINANT":
            return (
                15.0,
                "Foreign institutional buying is dominant.",
            )

        if market_bias == "DOMESTICALLY_SUPPORTED":
            return (
                8.0,
                "Domestic institutional buying is supporting the market.",
            )

        if market_bias == "MILD_BULLISH":
            return (
                5.0,
                "Institutional flows are mildly positive.",
            )

        if market_bias == "BEARISH":
            return (
                -20.0,
                "FII and DII institutional flows are jointly bearish.",
            )

        if market_bias == "FII_SELLING_DOMINANT":
            return (
                -15.0,
                "Foreign institutional selling is dominant.",
            )

        if market_bias == "DOMESTIC_SELLING_DOMINANT":
            return (
                -10.0,
                "Domestic institutional selling is dominant.",
            )

        if market_bias == "MILD_BEARISH":
            return (
                -5.0,
                "Institutional flows are mildly negative.",
            )

        return (
            0.0,
            "Institutional flows are neutral or mixed.",
        )

    def _calculate_institutional_score(
        self,
        options_section: dict[str, Any],
        india_vix: dict[str, Any],
        fii_dii: dict[str, Any],
    ) -> dict[str, Any]:
        contributions: list[dict[str, Any]] = []

        pcr_score, pcr_reason = self._score_pcr(
            options_section.get("pcr")
        )
        contributions.append(
            {
                "factor": "PCR",
                "score": pcr_score,
                "reason": pcr_reason,
            }
        )

        oi_score, oi_reason = self._score_oi(
            options_section.get("oi")
        )
        contributions.append(
            {
                "factor": "OI",
                "score": oi_score,
                "reason": oi_reason,
            }
        )

        max_pain_score, max_pain_reason = self._score_max_pain(
            options_section.get("max_pain")
        )
        contributions.append(
            {
                "factor": "MAX_PAIN",
                "score": max_pain_score,
                "reason": max_pain_reason,
            }
        )

        vix_score, vix_reason = self._score_vix(
            india_vix
        )
        contributions.append(
            {
                "factor": "INDIA_VIX",
                "score": vix_score,
                "reason": vix_reason,
            }
        )

        flow_score, flow_reason = self._score_institutional_flows(
            fii_dii
        )
        contributions.append(
            {
                "factor": "FII_DII",
                "score": flow_score,
                "reason": flow_reason,
            }
        )

        raw_score = sum(
            item["score"]
            for item in contributions
        )

        final_score = round(
            self._clamp_score(raw_score),
            2,
        )

        return {
            "score": final_score,
            "market_bias": self._bias_from_score(
                final_score
            ),
            "contributions": contributions,
        }

    def _write_snapshot_cache(
        self,
        symbol: str,
        snapshot: dict[str, Any],
    ) -> str | None:
        cache_key = symbol.strip().lower()

        if not cache_key:
            cache_key = "unknown"

        try:
            path = self.cache.write(
                namespace="market_snapshot",
                key=cache_key,
                payload=snapshot,
                ttl_seconds=self.snapshot_ttl_seconds,
            )

            return str(path)

        except JSONCacheError:
            return None

    def build(
        self,
        options_payload: dict[str, Any],
        india_vix_payload: dict[str, Any],
        fii_dii_payload: dict[str, Any],
    ) -> dict[str, Any]:
        options_payload = self._require_dictionary(
            options_payload,
            "Options analytics",
        )

        india_vix = self._require_dictionary(
            india_vix_payload,
            "India VIX",
        )

        fii_dii = self._require_dictionary(
            fii_dii_payload,
            "FII/DII",
        )

        options_section = self._extract_options_sections(
            options_payload
        )

        symbol = self._clean_symbol(
            options_section.get("symbol")
        )

        statuses = self._collect_statuses(
            options_section,
            india_vix,
            fii_dii,
        )

        overall_status = self._overall_data_status(
            statuses
        )

        confidence = self._confidence_label(
            statuses
        )

        confidence_values = (
            self._collect_source_confidences(
                options_section,
                india_vix,
                fii_dii,
            )
        )

        source_confidence = (
            self._average_source_confidence(
                confidence_values
            )
        )

        score_result = (
            self._calculate_institutional_score(
                options_section,
                india_vix,
                fii_dii,
            )
        )

        institutional_score = score_result[
            "score"
        ]
        market_bias = score_result[
            "market_bias"
        ]

        if overall_status == "NO_DATA":
            institutional_score = 0.0
            market_bias = "UNAVAILABLE"

        warnings = self._generate_warnings(
            options_section,
            india_vix,
            fii_dii,
            overall_status,
            source_confidence,
        )

        if confidence == "NONE":
            self._add_warning(
                warnings,
                "NO_DECISION_CONFIDENCE",
            )

        analytics_allowed = bool(
            options_section.get(
                "analytics_allowed",
                False,
            )
        )

        if overall_status == "NO_DATA":
            analytics_allowed = False

        snapshot: dict[str, Any] = {
            "snapshot_type": (
                "TRINETRA_UNIFIED_MARKET_SNAPSHOT"
            ),
            "schema_version": 1,
            "generated_at": self._utc_now(),
            "symbol": symbol,
            "market_status": overall_status,
            "data_status": overall_status,
            "analytics_allowed": analytics_allowed,
            "option_chain": options_section.get(
                "option_chain"
            ),
            "oi": options_section.get("oi"),
            "pcr": options_section.get("pcr"),
            "max_pain": options_section.get(
                "max_pain"
            ),
            "india_vix": india_vix,
            "fii_dii": fii_dii,
            "market_bias": market_bias,
            "institutional_score": (
                institutional_score
            ),
            "score_breakdown": score_result[
                "contributions"
            ],
            "confidence": confidence,
            "source_confidence": (
                source_confidence
            ),
            "source_statuses": {
                "options": statuses[0],
                "india_vix": statuses[1],
                "fii_dii": statuses[2],
            },
            "warnings": warnings,
            "cache_path": None,
        }

        snapshot["data_quality"] = {
            "overall_status": snapshot["data_status"],
            "source_confidence": snapshot["source_confidence"],
            "confidence_label": snapshot["confidence"],
            "analytics_allowed": snapshot["analytics_allowed"],
            "source_statuses": snapshot["source_statuses"],
            "warnings": snapshot["warnings"],
        }

        snapshot["data_quality"] = {
            "overall_status": snapshot["data_status"],
            "source_confidence": snapshot["source_confidence"],
            "confidence_label": snapshot["confidence"],
            "analytics_allowed": snapshot["analytics_allowed"],
            "source_statuses": snapshot["source_statuses"],
            "warnings": snapshot["warnings"],
        }

        cache_path = self._write_snapshot_cache(
            symbol,
            snapshot,
        )

        snapshot["cache_path"] = cache_path

        if cache_path is None:
            self._add_warning(
                snapshot["warnings"],
                "SNAPSHOT_CACHE_WRITE_FAILED",
            )

        return snapshot


if __name__ == "__main__":
    sample_options = {
        "symbol": "NIFTY",
        "data_status": "LIVE",
        "analytics_allowed": True,
        "errors": [],
        "option_chain": {
            "source": "NSE",
            "source_confidence": 100,
            "data_status": "LIVE",
        },
        "oi": {
            "total_call_oi_change": 500,
            "total_put_oi_change": 900,
        },
        "pcr": {
            "overall_pcr": 1.08,
        },
        "max_pain": {
            "underlying_value": 25050,
            "max_pain_strike": 25000,
        },
    }

    sample_vix = {
        "source": "TEST_FIXTURE",
        "source_confidence": 100,
        "data_status": "LIVE",
        "current": 14.5,
        "risk_regime": "LOW",
        "direction": "DOWN",
    }

    sample_flows = {
        "source": "TEST_FIXTURE",
        "source_confidence": 100,
        "data_status": "LIVE",
        "market_bias": "DOMESTICALLY_SUPPORTED",
        "fii": {
            "cash_net": -500,
        },
    }

    result = MarketSnapshotEngine().build(
        sample_options,
        sample_vix,
        sample_flows,
    )

    print("=" * 65)
    print("TRINETRA - UNIFIED MARKET SNAPSHOT")
    print("=" * 65)
    print(f"Symbol               : {result['symbol']}")
    print(f"Market Status        : {result['market_status']}")
    print(f"Market Bias          : {result['market_bias']}")
    print(
        f"Institutional Score  : "
        f"{result['institutional_score']}"
    )
    print(f"Confidence           : {result['confidence']}")
    print(
        f"Source Confidence    : "
        f"{result['source_confidence']}"
    )
    print(f"Warnings             : {result['warnings']}")
    print(f"Cache Path           : {result['cache_path']}")
