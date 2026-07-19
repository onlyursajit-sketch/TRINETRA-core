from __future__ import annotations

from typing import Any


class AIDecisionError(Exception):
    """Raised when AI Decision Hub input is invalid."""


class AIDecisionHub:
    """
    TRINETRA deterministic decision-support engine.

    Rules:
    - Verified inputs only
    - NO_DATA / low confidence par NO_TRADE
    - No standalone prediction
    - Every decision includes reasons and warnings
    """

    @staticmethod
    def _number(
        value: Any,
        default: float = 0.0,
    ) -> float:
        if isinstance(value, bool):
            return default

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _text(
        value: Any,
        default: str = "UNKNOWN",
    ) -> str:
        if value is None:
            return default

        cleaned = str(value).strip().upper()
        return cleaned or default

    @staticmethod
    def _clamp(
        value: float,
        low: float,
        high: float,
    ) -> float:
        return max(low, min(high, value))

    @staticmethod
    def _confidence_label(
        confidence_score: float,
    ) -> str:
        if confidence_score >= 80:
            return "HIGH"

        if confidence_score >= 60:
            return "MEDIUM"

        if confidence_score > 0:
            return "LOW"

        return "NONE"

    @staticmethod
    def _risk_label(
        risk_score: float,
    ) -> str:
        if risk_score >= 70:
            return "HIGH"

        if risk_score >= 35:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def _decision_from_score(
        score: float,
    ) -> str:
        if score >= 35:
            return "BUY_BIAS"

        if score <= -35:
            return "SELL_BIAS"

        return "WAIT"

    def decide(
        self,
        market_result: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(market_result, dict):
            raise AIDecisionError(
                "Market result must be a dictionary."
            )

        snapshot = market_result.get(
            "snapshot",
            {},
        )

        global_data = market_result.get(
            "global",
            {},
        )

        if not isinstance(snapshot, dict):
            snapshot = {}

        if not isinstance(global_data, dict):
            global_data = {}

        reasons: list[str] = []
        warnings: list[str] = []

        market_status = self._text(
            snapshot.get("market_status"),
            "NO_DATA",
        )

        analytics_allowed = bool(
            snapshot.get(
                "analytics_allowed",
                False,
            )
        )

        source_confidence = self._number(
            snapshot.get("source_confidence"),
            0.0,
        )

        global_confidence = self._number(
            global_data.get("source_confidence"),
            0.0,
        )

        global_bias = self._text(
            global_data.get("global_bias")
        )

        institutional_score = self._number(
            snapshot.get("institutional_score"),
            0.0,
        )

        snapshot_confidence = self._text(
            snapshot.get("confidence"),
            "NONE",
        )

        score = institutional_score
        risk_score = 0.0

        if global_bias == "STRONG_BULLISH":
            score += 20
            reasons.append(
                "Global markets are strongly bullish."
            )

        elif global_bias == "BULLISH":
            score += 12
            reasons.append(
                "Global markets support a bullish bias."
            )

        elif global_bias == "BEARISH":
            score -= 12
            reasons.append(
                "Global markets indicate bearish pressure."
            )

        elif global_bias == "STRONG_BEARISH":
            score -= 20
            reasons.append(
                "Global markets are strongly bearish."
            )

        elif global_bias == "NEUTRAL":
            reasons.append(
                "Global markets are directionally neutral."
            )

        vix = snapshot.get("india_vix")

        if isinstance(vix, dict):
            risk_regime = self._text(
                vix.get("risk_regime")
            )

            direction = self._text(
                vix.get("direction")
            )

            if risk_regime == "EXTREME":
                risk_score += 50
                warnings.append(
                    "EXTREME_VOLATILITY"
                )

            elif risk_regime == "HIGH":
                risk_score += 30
                warnings.append(
                    "HIGH_VOLATILITY"
                )

            elif risk_regime == "MODERATE":
                risk_score += 15

            if direction == "UP":
                risk_score += 10
                reasons.append(
                    "India VIX is rising."
                )

            elif direction == "DOWN":
                risk_score -= 5
                reasons.append(
                    "India VIX is declining."
                )

        fii_dii = snapshot.get("fii_dii")

        if isinstance(fii_dii, dict):
            flow_bias = self._text(
                fii_dii.get("market_bias")
            )

            if flow_bias in {
                "BULLISH",
                "FII_BUYING_DOMINANT",
            }:
                score += 10
                reasons.append(
                    "Institutional flows are supportive."
                )

            elif flow_bias in {
                "BEARISH",
                "FII_SELLING_DOMINANT",
            }:
                score -= 10
                reasons.append(
                    "Institutional flows are negative."
                )

            elif flow_bias == "DOMESTICALLY_SUPPORTED":
                score += 5
                reasons.append(
                    "Domestic institutions are supporting the market."
                )

        max_pain = snapshot.get("max_pain")

        if isinstance(max_pain, dict):
            max_pain_strike = self._number(
                max_pain.get("max_pain_strike"),
                0.0,
            )
            spot_price = self._number(
                max_pain.get("spot_price"),
                0.0,
            )

            if max_pain_strike > 0:
                if spot_price > 0:
                    distance_pct = abs(
                        spot_price - max_pain_strike
                    ) / max_pain_strike * 100

                    reasons.append(
                        f"Max Pain is {max_pain_strike:.0f}; "
                        f"spot is {distance_pct:.2f}% away."
                    )
                else:
                    reasons.append(
                        f"Max Pain is positioned near "
                        f"{max_pain_strike:.0f}."
                    )

        pcr = snapshot.get("pcr")

        if isinstance(pcr, dict):
            overall_pcr = self._number(
                pcr.get("overall_pcr"),
                0.0,
            )

            if 1.0 <= overall_pcr <= 1.2:
                score += 8
                reasons.append(
                    "PCR is in a supportive bullish range."
                )

            elif overall_pcr < 0.8:
                score -= 8
                reasons.append(
                    "PCR indicates bearish positioning."
                )

            elif overall_pcr > 1.5:
                warnings.append(
                    "CROWDED_PCR_POSITIONING"
                )


        oi = snapshot.get("oi")

        if isinstance(oi, dict):
            oi_bias = self._text(
                oi.get("market_bias"),
            )

            if oi_bias == "BULLISH":
                score += 10
                reasons.append(
                    "Open interest structure is bullish."
                )

            elif oi_bias == "BEARISH":
                score -= 10
                reasons.append(
                    "Open interest structure is bearish."
                )

        volume_analysis = snapshot.get("volume_analysis")

        if isinstance(volume_analysis, dict):
            volume_bias = self._text(
                volume_analysis.get("market_bias"),
            )

            if volume_bias == "BULLISH":
                score += 8
                reasons.append(
                    "Volume participation supports bullish momentum."
                )

            elif volume_bias == "BEARISH":
                score -= 8
                reasons.append(
                    "Volume participation supports bearish momentum."
                )

        score = round(
            self._clamp(
                score,
                -100.0,
                100.0,
            ),
            2,
        )

        risk_score = round(
            self._clamp(
                risk_score,
                0.0,
                100.0,
            ),
            2,
        )

        combined_confidence = round(
            (
                source_confidence
                + global_confidence
            ) / 2,
            2,
        )

        no_trade_reasons: list[str] = []

        if market_status in {
            "NO_DATA",
            "UNKNOWN",
        }:
            no_trade_reasons.append(
                "Market snapshot is unavailable."
            )

        if not analytics_allowed:
            no_trade_reasons.append(
                "Analytics are blocked."
            )

        if combined_confidence < 50:
            no_trade_reasons.append(
                "Combined source confidence is below 50%."
            )

        if snapshot_confidence == "NONE":
            no_trade_reasons.append(
                "Snapshot decision confidence is unavailable."
            )

        snapshot_warnings = snapshot.get(
            "warnings",
            [],
        )

        if isinstance(snapshot_warnings, list):
            for warning in snapshot_warnings:
                if isinstance(warning, str):
                    if warning not in warnings:
                        warnings.append(warning)

        global_warnings = global_data.get(
            "warnings",
            [],
        )

        if isinstance(global_warnings, list):
            for warning in global_warnings:
                if isinstance(warning, str):
                    if warning not in warnings:
                        warnings.append(warning)

        if no_trade_reasons:
            decision = "NO_TRADE"
            action = "WAIT_FOR_VERIFIED_DATA"
            confidence_score = 0.0
            reasons.extend(no_trade_reasons)

        else:
            decision = self._decision_from_score(
                score
            )

            confidence_score = round(
                self._clamp(
                    combined_confidence
                    - (risk_score * 0.25),
                    0.0,
                    100.0,
                ),
                2,
            )

            if decision == "BUY_BIAS":
                action = "WAIT_FOR_LONG_CONFIRMATION"

            elif decision == "SELL_BIAS":
                action = "WAIT_FOR_SHORT_CONFIRMATION"

            else:
                action = "WAIT"

        trade_quality_score = (
            0.0
            if decision == "NO_TRADE"
            else round(
                self._clamp(
                    (confidence_score * 0.70)
                    + ((100.0 - risk_score) * 0.30),
                    0.0,
                    100.0,
                ),
                2,
            )
        )

        explanation = {
            "summary": (
                f"{decision} with {self._confidence_label(confidence_score)} "
                f"confidence and {self._risk_label(risk_score)} risk."
            ),
            "reasons": list(reasons),
            "warnings": list(warnings),
        }

        return {
            "engine": "TRINETRA_AI_DECISION_HUB",
            "decision": decision,
            "action": action,
            "score": score,
            "confidence_score": confidence_score,
            "confidence": self._confidence_label(
                confidence_score
            ),
            "risk_score": risk_score,
            "trade_quality_score": trade_quality_score,
            "risk": self._risk_label(
                risk_score
            ),
            "analytics_allowed": analytics_allowed,
            "market_status": market_status,
            "global_bias": global_bias,
            "institutional_score": (
                institutional_score
            ),
            "reasons": reasons,
            "warnings": warnings,
            "explanation": explanation,
            "rule": (
                "Decision support only. "
                "No standalone prediction."
            ),
        }


if __name__ == "__main__":
    fixture = {
        "global": {
            "global_bias": "BULLISH",
            "source_confidence": 90,
            "warnings": [],
        },
        "snapshot": {
            "market_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "confidence": "HIGH",
            "institutional_score": 40,
            "warnings": [],
            "pcr": {
                "overall_pcr": 1.08,
            },
            "india_vix": {
                "risk_regime": "LOW",
                "direction": "DOWN",
            },
            "fii_dii": {
                "market_bias": (
                    "DOMESTICALLY_SUPPORTED"
                ),
            },
        },
    }

    result = AIDecisionHub().decide(
        fixture
    )

    print("=" * 68)
    print("TRINETRA - AI DECISION HUB")
    print("=" * 68)

    for key, value in result.items():
        print(f"{key}: {value}")
