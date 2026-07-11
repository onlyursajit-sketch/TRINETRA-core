from __future__ import annotations

from typing import Any


class MaxPainEngineError(Exception):
    """Raised when Max Pain analysis cannot be completed."""


class MaxPainEngine:
    """
    TRINETRA Max Pain Engine.

    Calculates the option-writer payout at every available strike:

    Call payout:
        max(settlement_strike - option_strike, 0) * Call OI

    Put payout:
        max(option_strike - settlement_strike, 0) * Put OI

    The settlement strike with minimum total payout is Max Pain.
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

    def _validate_payload(
        self,
        payload: dict[str, Any],
    ) -> None:
        if not isinstance(payload, dict):
            raise MaxPainEngineError(
                "Option-chain payload must be a dictionary."
            )

        if payload.get("data_status") == "NO_DATA":
            raise MaxPainEngineError(
                "Max Pain analysis blocked because data status is NO_DATA."
            )

        records = payload.get("records")

        if not isinstance(records, list):
            raise MaxPainEngineError(
                "Option-chain records are missing or invalid."
            )

        if not records:
            raise MaxPainEngineError(
                "Option-chain records are empty."
            )

    def _filter_expiry(
        self,
        payload: dict[str, Any],
        expiry: str | None,
    ) -> tuple[str | None, list[dict[str, Any]]]:
        selected_expiry = expiry or payload.get("nearest_expiry")
        records = payload["records"]

        if selected_expiry is None:
            return None, records

        filtered_records = [
            row
            for row in records
            if row.get("expiry_date") == selected_expiry
        ]

        if not filtered_records:
            raise MaxPainEngineError(
                f"No option-chain records found for expiry "
                f"{selected_expiry}."
            )

        return selected_expiry, filtered_records

    def analyse(
        self,
        payload: dict[str, Any],
        expiry: str | None = None,
    ) -> dict[str, Any]:
        self._validate_payload(payload)

        selected_expiry, records = self._filter_expiry(
            payload,
            expiry,
        )

        option_rows: list[dict[str, float]] = []

        for row in records:
            strike = self._number(
                row.get("strike_price")
            )

            if strike <= 0:
                continue

            ce = row.get("ce")
            pe = row.get("pe")

            call_oi = 0.0
            put_oi = 0.0

            if isinstance(ce, dict):
                call_oi = self._number(
                    ce.get("openInterest")
                )

            if isinstance(pe, dict):
                put_oi = self._number(
                    pe.get("openInterest")
                )

            option_rows.append(
                {
                    "strike": strike,
                    "call_oi": call_oi,
                    "put_oi": put_oi,
                }
            )

        if not option_rows:
            raise MaxPainEngineError(
                "No valid strike data available."
            )

        candidate_strikes = sorted(
            {
                row["strike"]
                for row in option_rows
            }
        )

        pain_table: list[dict[str, float]] = []

        for settlement_strike in candidate_strikes:
            total_call_payout = 0.0
            total_put_payout = 0.0

            for option in option_rows:
                option_strike = option["strike"]

                call_intrinsic = max(
                    settlement_strike - option_strike,
                    0.0,
                )

                put_intrinsic = max(
                    option_strike - settlement_strike,
                    0.0,
                )

                total_call_payout += (
                    call_intrinsic
                    * option["call_oi"]
                )

                total_put_payout += (
                    put_intrinsic
                    * option["put_oi"]
                )

            total_payout = (
                total_call_payout
                + total_put_payout
            )

            pain_table.append(
                {
                    "settlement_strike": settlement_strike,
                    "call_payout": total_call_payout,
                    "put_payout": total_put_payout,
                    "total_payout": total_payout,
                }
            )

        sorted_pain = sorted(
            pain_table,
            key=lambda item: (
                item["total_payout"],
                item["settlement_strike"],
            ),
        )

        max_pain_row = sorted_pain[0]
        max_pain_strike = max_pain_row[
            "settlement_strike"
        ]

        underlying_value = self._number(
            payload.get("underlying_value")
        )

        atm_strike = self._number(
            payload.get("atm_strike")
        )

        distance_from_underlying = None
        distance_from_atm = None

        if underlying_value > 0:
            distance_from_underlying = round(
                max_pain_strike - underlying_value,
                2,
            )

        if atm_strike > 0:
            distance_from_atm = round(
                max_pain_strike - atm_strike,
                2,
            )

        data_status = payload.get("data_status")

        if data_status == "LIVE":
            confidence = "HIGH"
        elif data_status == "STALE":
            confidence = "LOW"
        else:
            confidence = "MEDIUM"

        return {
            "symbol": payload.get("symbol"),
            "source": payload.get("source"),
            "data_status": data_status,
            "expiry": selected_expiry,
            "underlying_value": (
                underlying_value
                if underlying_value > 0
                else None
            ),
            "atm_strike": (
                atm_strike
                if atm_strike > 0
                else None
            ),
            "max_pain_strike": max_pain_strike,
            "minimum_total_payout": max_pain_row[
                "total_payout"
            ],
            "call_payout_at_max_pain": max_pain_row[
                "call_payout"
            ],
            "put_payout_at_max_pain": max_pain_row[
                "put_payout"
            ],
            "distance_from_underlying": (
                distance_from_underlying
            ),
            "distance_from_atm": distance_from_atm,
            "nearest_pain_levels": sorted_pain[:5],
            "pain_table": pain_table,
            "strikes_analysed": len(candidate_strikes),
            "confidence": confidence,
            "risk_note": (
                "Max Pain is a positioning reference, "
                "not a guaranteed expiry settlement level."
            ),
        }


if __name__ == "__main__":
    import json
    from pathlib import Path

    cache_path = Path(
        "cache/option_chain/nifty_latest.json"
    )

    if not cache_path.exists():
        raise SystemExit(
            "No cached NIFTY option-chain file found."
        )

    with cache_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        option_chain = json.load(file)

    engine = MaxPainEngine()
    result = engine.analyse(option_chain)

    print("=" * 60)
    print("TRINETRA - MAX PAIN ENGINE")
    print("=" * 60)
    print(f"Symbol                 : {result['symbol']}")
    print(f"Expiry                 : {result['expiry']}")
    print(f"Data Status            : {result['data_status']}")
    print(f"Underlying             : {result['underlying_value']}")
    print(f"ATM Strike             : {result['atm_strike']}")
    print(f"Max Pain Strike        : {result['max_pain_strike']}")
    print(
        f"Distance from ATM      : "
        f"{result['distance_from_atm']}"
    )
    print(
        f"Distance from Underlying: "
        f"{result['distance_from_underlying']}"
    )
    print(
        f"Minimum Total Payout   : "
        f"{result['minimum_total_payout']}"
    )
    print(f"Confidence             : {result['confidence']}")
