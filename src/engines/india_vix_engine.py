from __future__ import annotations

from datetime import datetime
from typing import Any


class IndiaVIXEngineError(Exception):
    """Raised when India VIX analysis cannot be completed."""


class IndiaVIXEngine:
    """
    TRINETRA India VIX Intelligence Engine.

    Expected normalized payload:

    {
        "symbol": "INDIA_VIX",
        "source": "NSE",
        "data_status": "LIVE",
        "previous_close": 14.20,
        "open": 14.35,
        "high": 15.10,
        "low": 14.05,
        "current": 14.85,
        "timestamp": "...",
        "source_confidence": 100
    }

    Rules:
    - NO_DATA is blocked.
    - STALE data is accepted with low confidence.
    - No prediction is generated.
    - Output provides verified calculation and interpretation only.
    """

    @staticmethod
    def _number(value: Any) -> float | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _regime(current: float) -> dict[str, str]:
        if current < 12:
            return {
                "risk_regime": "VERY_LOW",
                "market_environment": "COMPLACENT",
                "impact": (
                    "Volatility is very low. Premiums may remain compressed, "
                    "but sudden volatility expansion risk should not be ignored."
                ),
            }

        if current < 15:
            return {
                "risk_regime": "LOW",
                "market_environment": "STABLE",
                "impact": (
                    "Market volatility is relatively low. "
                    "Price movement may remain controlled."
                ),
            }

        if current < 18:
            return {
                "risk_regime": "MODERATE",
                "market_environment": "CAUTIOUS",
                "impact": (
                    "Volatility is moderate. Wider intraday movement and "
                    "higher option premiums may be visible."
                ),
            }

        if current < 25:
            return {
                "risk_regime": "HIGH",
                "market_environment": "RISK_OFF",
                "impact": (
                    "Volatility is elevated. Position sizing and stop-loss "
                    "discipline become more important."
                ),
            }

        return {
            "risk_regime": "EXTREME",
            "market_environment": "STRESS",
            "impact": (
                "Volatility is extremely high. Large price swings, gaps and "
                "rapid option-premium changes are possible."
            ),
        }

    @staticmethod
    def _direction_impact(
        difference: float,
        percentage_change: float | None,
    ) -> dict[str, str]:
        if difference > 0:
            if percentage_change is not None and percentage_change >= 10:
                strength = "SHARP_RISE"
            else:
                strength = "RISING"

            return {
                "direction": "UP",
                "volatility_signal": strength,
                "direction_impact": (
                    "Volatility is increasing, indicating rising uncertainty "
                    "and potentially wider market ranges."
                ),
            }

        if difference < 0:
            if percentage_change is not None and percentage_change <= -10:
                strength = "SHARP_FALL"
            else:
                strength = "FALLING"

            return {
                "direction": "DOWN",
                "volatility_signal": strength,
                "direction_impact": (
                    "Volatility is declining, indicating reduced uncertainty "
                    "and potentially more stable price action."
                ),
            }

        return {
            "direction": "FLAT",
            "volatility_signal": "UNCHANGED",
            "direction_impact": (
                "Volatility is unchanged from the previous close."
            ),
        }

    def _validate_payload(
        self,
        payload: dict[str, Any],
    ) -> None:
        if not isinstance(payload, dict):
            raise IndiaVIXEngineError(
                "India VIX payload must be a dictionary."
            )

        if payload.get("data_status") == "NO_DATA":
            raise IndiaVIXEngineError(
                "India VIX analysis blocked because data status is NO_DATA."
            )

        previous_close = self._number(
            payload.get("previous_close")
        )
        current = self._number(
            payload.get("current")
        )

        if previous_close is None or previous_close <= 0:
            raise IndiaVIXEngineError(
                "Valid previous_close is required."
            )

        if current is None or current <= 0:
            raise IndiaVIXEngineError(
                "Valid current value is required."
            )

    def analyse(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_payload(payload)

        previous_close = self._number(
            payload.get("previous_close")
        )
        current = self._number(
            payload.get("current")
        )

        assert previous_close is not None
        assert current is not None

        open_value = self._number(
            payload.get("open")
        )
        high = self._number(
            payload.get("high")
        )
        low = self._number(
            payload.get("low")
        )

        difference = round(
            current - previous_close,
            4,
        )

        percentage_change = round(
            (difference / previous_close) * 100,
            4,
        )

        regime = self._regime(current)

        direction = self._direction_impact(
            difference,
            percentage_change,
        )

        data_status = payload.get("data_status", "UNKNOWN")

        source_confidence = self._number(
            payload.get("source_confidence")
        )

        if data_status == "LIVE":
            confidence = "HIGH"
        elif data_status == "STALE":
            confidence = "LOW"
        else:
            confidence = "MEDIUM"

        return {
            "symbol": payload.get(
                "symbol",
                "INDIA_VIX",
            ),
            "source": payload.get("source"),
            "source_confidence": (
                source_confidence
                if source_confidence is not None
                else 0.0
            ),
            "data_status": data_status,
            "timestamp": payload.get(
                "timestamp",
                datetime.now().astimezone().isoformat(),
            ),
            "previous_close": previous_close,
            "open": open_value,
            "high": high,
            "low": low,
            "current": current,
            "difference": difference,
            "percentage_change": percentage_change,
            "direction": direction["direction"],
            "volatility_signal": direction[
                "volatility_signal"
            ],
            "risk_regime": regime["risk_regime"],
            "market_environment": regime[
                "market_environment"
            ],
            "impact": regime["impact"],
            "direction_impact": direction[
                "direction_impact"
            ],
            "confidence": confidence,
            "risk_note": (
                "India VIX measures expected market volatility. "
                "It is not a standalone directional prediction."
            ),
        }


if __name__ == "__main__":
    sample_payload = {
        "symbol": "INDIA_VIX",
        "source": "TEST_FIXTURE",
        "source_confidence": 100,
        "data_status": "LIVE",
        "previous_close": 14.20,
        "open": 14.35,
        "high": 15.10,
        "low": 14.05,
        "current": 14.85,
        "timestamp": datetime.now().astimezone().isoformat(),
    }

    engine = IndiaVIXEngine()
    result = engine.analyse(sample_payload)

    print("=" * 60)
    print("TRINETRA - INDIA VIX INTELLIGENCE")
    print("=" * 60)
    print(f"Previous Close     : {result['previous_close']}")
    print(f"Current            : {result['current']}")
    print(f"Difference         : {result['difference']}")
    print(f"Percentage Change  : {result['percentage_change']}%")
    print(f"Risk Regime        : {result['risk_regime']}")
    print(f"Direction          : {result['direction']}")
    print(f"Impact             : {result['impact']}")
    print(f"Data Status        : {result['data_status']}")
    print(f"Confidence         : {result['confidence']}")
