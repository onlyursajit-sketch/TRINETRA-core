from __future__ import annotations

from collections import Counter
from typing import Any


class OIEngineError(Exception):
    """Raised when option-chain data cannot be analysed."""


class OIEngine:
    """
    TRINETRA Open Interest Engine.

    Default behaviour:
    - Analyses only the nearest expiry.
    - Blocks NO_DATA payloads.
    - Allows STALE payloads but preserves the warning status.
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
    def _classify_buildup(
        price_change: float,
        oi_change: float,
    ) -> str:
        if price_change > 0 and oi_change > 0:
            return "LONG_BUILDUP"

        if price_change < 0 and oi_change > 0:
            return "SHORT_BUILDUP"

        if price_change < 0 and oi_change < 0:
            return "LONG_UNWINDING"

        if price_change > 0 and oi_change < 0:
            return "SHORT_COVERING"

        return "NEUTRAL"

    def _validate_payload(
        self,
        payload: dict[str, Any],
    ) -> None:
        if not isinstance(payload, dict):
            raise OIEngineError(
                "Option-chain payload must be a dictionary."
            )

        data_status = payload.get("data_status")

        if data_status == "NO_DATA":
            raise OIEngineError(
                "OI analysis blocked because option-chain status is NO_DATA."
            )

        records = payload.get("records")

        if not isinstance(records, list):
            raise OIEngineError(
                "Option-chain records are missing or invalid."
            )

        if not records:
            raise OIEngineError(
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

        filtered = [
            row
            for row in records
            if row.get("expiry_date") == selected_expiry
        ]

        if not filtered:
            raise OIEngineError(
                f"No option-chain records found for expiry "
                f"{selected_expiry}."
            )

        return selected_expiry, filtered

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

        total_call_oi = 0.0
        total_put_oi = 0.0
        total_call_oi_change = 0.0
        total_put_oi_change = 0.0

        call_levels: list[dict[str, Any]] = []
        put_levels: list[dict[str, Any]] = []
        buildup_rows: list[dict[str, Any]] = []
        buildup_counter: Counter[str] = Counter()

        for row in records:
            strike = self._number(row.get("strike_price"))

            ce = row.get("ce")
            pe = row.get("pe")

            if isinstance(ce, dict):
                call_oi = self._number(
                    ce.get("openInterest")
                )
                call_oi_change = self._number(
                    ce.get("changeinOpenInterest")
                )
                call_price_change = self._number(
                    ce.get("change")
                )

                total_call_oi += call_oi
                total_call_oi_change += call_oi_change

                call_levels.append(
                    {
                        "strike": strike,
                        "open_interest": call_oi,
                        "oi_change": call_oi_change,
                        "volume": self._number(
                            ce.get("totalTradedVolume")
                        ),
                        "last_price": self._number(
                            ce.get("lastPrice")
                        ),
                    }
                )

                call_classification = self._classify_buildup(
                    call_price_change,
                    call_oi_change,
                )

                buildup_counter[
                    f"CE_{call_classification}"
                ] += 1

                buildup_rows.append(
                    {
                        "strike": strike,
                        "option_type": "CE",
                        "price_change": call_price_change,
                        "oi_change": call_oi_change,
                        "classification": call_classification,
                    }
                )

            if isinstance(pe, dict):
                put_oi = self._number(
                    pe.get("openInterest")
                )
                put_oi_change = self._number(
                    pe.get("changeinOpenInterest")
                )
                put_price_change = self._number(
                    pe.get("change")
                )

                total_put_oi += put_oi
                total_put_oi_change += put_oi_change

                put_levels.append(
                    {
                        "strike": strike,
                        "open_interest": put_oi,
                        "oi_change": put_oi_change,
                        "volume": self._number(
                            pe.get("totalTradedVolume")
                        ),
                        "last_price": self._number(
                            pe.get("lastPrice")
                        ),
                    }
                )

                put_classification = self._classify_buildup(
                    put_price_change,
                    put_oi_change,
                )

                buildup_counter[
                    f"PE_{put_classification}"
                ] += 1

                buildup_rows.append(
                    {
                        "strike": strike,
                        "option_type": "PE",
                        "price_change": put_price_change,
                        "oi_change": put_oi_change,
                        "classification": put_classification,
                    }
                )

        if not call_levels and not put_levels:
            raise OIEngineError(
                "No valid CE or PE records were available."
            )

        sorted_calls = sorted(
            call_levels,
            key=lambda item: item["open_interest"],
            reverse=True,
        )

        sorted_puts = sorted(
            put_levels,
            key=lambda item: item["open_interest"],
            reverse=True,
        )

        highest_call = sorted_calls[0] if sorted_calls else None
        highest_put = sorted_puts[0] if sorted_puts else None

        return {
            "symbol": payload.get("symbol"),
            "source": payload.get("source"),
            "data_status": payload.get("data_status"),
            "expiry": selected_expiry,
            "underlying_value": payload.get("underlying_value"),
            "atm_strike": payload.get("atm_strike"),
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "total_call_oi_change": total_call_oi_change,
            "total_put_oi_change": total_put_oi_change,
            "highest_call_oi": highest_call,
            "highest_put_oi": highest_put,
            "resistance": (
                highest_call["strike"]
                if highest_call
                else None
            ),
            "support": (
                highest_put["strike"]
                if highest_put
                else None
            ),
            "top_call_oi_levels": sorted_calls[:5],
            "top_put_oi_levels": sorted_puts[:5],
            "buildup_summary": dict(buildup_counter),
            "buildup_records": buildup_rows,
            "records_analysed": len(records),
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

    with cache_path.open("r", encoding="utf-8") as file:
        option_chain = json.load(file)

    engine = OIEngine()
    result = engine.analyse(option_chain)

    print("=" * 60)
    print("TRINETRA - OI ENGINE")
    print("=" * 60)
    print(f"Symbol             : {result['symbol']}")
    print(f"Expiry             : {result['expiry']}")
    print(f"Data Status        : {result['data_status']}")
    print(f"Total Call OI      : {result['total_call_oi']}")
    print(f"Total Put OI       : {result['total_put_oi']}")
    print(f"Call OI Change     : {result['total_call_oi_change']}")
    print(f"Put OI Change      : {result['total_put_oi_change']}")
    print(f"Resistance         : {result['resistance']}")
    print(f"Support            : {result['support']}")
    print(f"Records Analysed   : {result['records_analysed']}")
