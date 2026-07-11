from __future__ import annotations

from typing import Any


class PCREngineError(Exception):
    """Raised when PCR analysis cannot be completed."""


class PCREngine:
    """
    TRINETRA Put-Call Ratio Engine.

    Calculates:
    - Overall OI PCR
    - OI-change PCR
    - Strike-wise PCR
    - ATM PCR
    - Market interpretation
    """

    @staticmethod
    def _number(value: Any) -> float:
        if isinstance(value, bool):
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _safe_ratio(
        numerator: float,
        denominator: float,
    ) -> float | None:
        if denominator <= 0:
            return None

        return round(numerator / denominator, 4)

    @staticmethod
    def _interpret(pcr: float | None) -> dict[str, str]:
        if pcr is None:
            return {
                "bias": "UNAVAILABLE",
                "signal": "NO_SIGNAL",
                "risk_note": "Call OI is zero or unavailable.",
            }

        if pcr < 0.60:
            return {
                "bias": "EXTREME_BEARISH",
                "signal": "STRONG_SELL_BIAS",
                "risk_note": "Extreme positioning; reversal risk remains.",
            }

        if pcr < 0.80:
            return {
                "bias": "BEARISH",
                "signal": "SELL_BIAS",
                "risk_note": "Confirm with OI buildup and price action.",
            }

        if pcr < 1.00:
            return {
                "bias": "NEUTRAL_BEARISH",
                "signal": "WAIT",
                "risk_note": "No strong directional edge.",
            }

        if pcr <= 1.20:
            return {
                "bias": "BULLISH",
                "signal": "BUY_BIAS",
                "risk_note": "Confirm with support and volatility.",
            }

        return {
            "bias": "OVER_BULLISH",
            "signal": "REVERSAL_WATCH",
            "risk_note": "Crowded bullish positioning may reverse.",
        }

    def _validate_payload(
        self,
        payload: dict[str, Any],
    ) -> None:
        if not isinstance(payload, dict):
            raise PCREngineError(
                "OI payload must be a dictionary."
            )

        if payload.get("data_status") == "NO_DATA":
            raise PCREngineError(
                "PCR analysis blocked because data status is NO_DATA."
            )

        if "total_call_oi" not in payload:
            raise PCREngineError(
                "Missing total_call_oi."
            )

        if "total_put_oi" not in payload:
            raise PCREngineError(
                "Missing total_put_oi."
            )

    def analyse(
        self,
        oi_payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_payload(oi_payload)

        total_call_oi = self._number(
            oi_payload.get("total_call_oi")
        )
        total_put_oi = self._number(
            oi_payload.get("total_put_oi")
        )

        total_call_oi_change = self._number(
            oi_payload.get("total_call_oi_change")
        )
        total_put_oi_change = self._number(
            oi_payload.get("total_put_oi_change")
        )

        overall_pcr = self._safe_ratio(
            total_put_oi,
            total_call_oi,
        )

        oi_change_pcr = self._safe_ratio(
            total_put_oi_change,
            total_call_oi_change,
        )

        atm_strike = self._number(
            oi_payload.get("atm_strike")
        )

        call_levels = oi_payload.get(
            "top_call_oi_levels",
            [],
        )
        put_levels = oi_payload.get(
            "top_put_oi_levels",
            [],
        )

        call_map = {
            self._number(item.get("strike")): self._number(
                item.get("open_interest")
            )
            for item in call_levels
            if isinstance(item, dict)
        }

        put_map = {
            self._number(item.get("strike")): self._number(
                item.get("open_interest")
            )
            for item in put_levels
            if isinstance(item, dict)
        }

        all_strikes = sorted(
            set(call_map) | set(put_map)
        )

        strike_wise_pcr: list[dict[str, Any]] = []

        bullish_strikes = 0
        bearish_strikes = 0

        for strike in all_strikes:
            call_oi = call_map.get(strike, 0.0)
            put_oi = put_map.get(strike, 0.0)

            strike_pcr = self._safe_ratio(
                put_oi,
                call_oi,
            )

            if strike_pcr is not None:
                if strike_pcr >= 1.0:
                    bullish_strikes += 1
                else:
                    bearish_strikes += 1

            strike_wise_pcr.append(
                {
                    "strike": strike,
                    "call_oi": call_oi,
                    "put_oi": put_oi,
                    "pcr": strike_pcr,
                }
            )

        atm_call_oi = call_map.get(atm_strike, 0.0)
        atm_put_oi = put_map.get(atm_strike, 0.0)

        atm_pcr = self._safe_ratio(
            atm_put_oi,
            atm_call_oi,
        )

        interpretation = self._interpret(
            overall_pcr
        )

        confidence = "LOW"

        if overall_pcr is not None:
            if oi_payload.get("data_status") == "LIVE":
                confidence = "HIGH"
            elif oi_payload.get("data_status") == "STALE":
                confidence = "LOW"
            else:
                confidence = "MEDIUM"

        return {
            "symbol": oi_payload.get("symbol"),
            "source": oi_payload.get("source"),
            "data_status": oi_payload.get("data_status"),
            "expiry": oi_payload.get("expiry"),
            "underlying_value": oi_payload.get(
                "underlying_value"
            ),
            "atm_strike": atm_strike,
            "overall_pcr": overall_pcr,
            "oi_change_pcr": oi_change_pcr,
            "atm_pcr": atm_pcr,
            "bullish_strikes": bullish_strikes,
            "bearish_strikes": bearish_strikes,
            "market_bias": interpretation["bias"],
            "signal": interpretation["signal"],
            "risk_note": interpretation["risk_note"],
            "confidence": confidence,
            "strike_wise_pcr": strike_wise_pcr,
        }


if __name__ == "__main__":
    raise SystemExit(
        "PCR Engine ko OI Engine payload ke saath run karein."
    )
