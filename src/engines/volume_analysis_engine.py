from __future__ import annotations

from typing import Any


class VolumeAnalysisError(Exception):
    """Raised when option-chain volume analysis cannot be completed."""


class VolumeAnalysisEngine:
    """Analyse call and put trading volume from normalized option-chain data."""

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return max(0.0, float(value or 0))
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _option_volume(cls, option: Any) -> float:
        if not isinstance(option, dict):
            return 0.0

        return cls._number(
            option.get(
                "totalTradedVolume",
                option.get("volume", option.get("total_traded_volume", 0)),
            )
        )

    def analyse(
        self,
        option_chain: dict[str, Any],
        expiry: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(option_chain, dict):
            raise VolumeAnalysisError("Option-chain payload must be a dictionary.")

        records = option_chain.get("records", [])
        if not isinstance(records, list):
            raise VolumeAnalysisError("Option-chain records must be a list.")

        call_volume = 0.0
        put_volume = 0.0
        strike_rows: list[dict[str, Any]] = []

        for row in records:
            if not isinstance(row, dict):
                continue

            row_expiry = row.get("expiry_date", row.get("expiryDate"))
            if expiry is not None and row_expiry != expiry:
                continue

            ce = row.get("ce", row.get("CE", {}))
            pe = row.get("pe", row.get("PE", {}))

            ce_volume = self._option_volume(ce)
            pe_volume = self._option_volume(pe)

            call_volume += ce_volume
            put_volume += pe_volume

            strike_rows.append(
                {
                    "strike_price": row.get(
                        "strike_price",
                        row.get("strikePrice"),
                    ),
                    "call_volume": ce_volume,
                    "put_volume": pe_volume,
                    "total_volume": ce_volume + pe_volume,
                }
            )

        total_volume = call_volume + put_volume

        if total_volume == 0:
            market_bias = "NEUTRAL"
        elif put_volume > call_volume:
            market_bias = "BULLISH"
        elif call_volume > put_volume:
            market_bias = "BEARISH"
        else:
            market_bias = "NEUTRAL"

        top_strikes = sorted(
            strike_rows,
            key=lambda item: item["total_volume"],
            reverse=True,
        )[:5]

        return {
            "call_volume": round(call_volume, 2),
            "put_volume": round(put_volume, 2),
            "total_volume": round(total_volume, 2),
            "put_call_volume_ratio": (
                round(put_volume / call_volume, 2)
                if call_volume > 0
                else None
            ),
            "market_bias": market_bias,
            "volume_bullish": market_bias == "BULLISH",
            "top_volume_strikes": top_strikes,
            "analysed_records": len(strike_rows),
        }
