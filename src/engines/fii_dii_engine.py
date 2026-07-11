from __future__ import annotations

from datetime import datetime
from typing import Any


class FIIDIIEngineError(Exception):
    """Raised when FII/DII analysis cannot be completed."""


class FIIDIIEngine:
    """
    TRINETRA FII/DII Intelligence Engine.

    Expected normalized payload:

    {
        "source": "NSE",
        "source_confidence": 100,
        "data_status": "LIVE",
        "trade_date": "2026-07-11",
        "fii": {
            "cash_buy": 12500,
            "cash_sell": 13800,
            "index_futures_net": -750,
            "stock_futures_net": 420,
            "index_options_net": -300
        },
        "dii": {
            "cash_buy": 11200,
            "cash_sell": 9600
        }
    }

    Amounts are assumed to be in INR crore.
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
    def _position(net_amount: float) -> str:
        if net_amount > 0:
            return "NET_BUY"

        if net_amount < 0:
            return "NET_SELL"

        return "NEUTRAL"

    @staticmethod
    def _impact(
        participant: str,
        net_amount: float,
    ) -> str:
        absolute_amount = abs(net_amount)

        if participant == "FII":
            if net_amount >= 2000:
                return "STRONG_BULLISH"
            if net_amount >= 500:
                return "BULLISH"
            if net_amount > 0:
                return "MILD_BULLISH"
            if net_amount <= -2000:
                return "STRONG_BEARISH"
            if net_amount <= -500:
                return "BEARISH"
            if net_amount < 0:
                return "MILD_BEARISH"
            return "NEUTRAL"

        if absolute_amount >= 2000:
            return (
                "STRONG_DOMESTIC_SUPPORT"
                if net_amount > 0
                else "STRONG_DOMESTIC_SELLING"
            )

        if absolute_amount >= 500:
            return (
                "DOMESTIC_SUPPORT"
                if net_amount > 0
                else "DOMESTIC_SELLING"
            )

        if net_amount > 0:
            return "MILD_DOMESTIC_SUPPORT"

        if net_amount < 0:
            return "MILD_DOMESTIC_SELLING"

        return "NEUTRAL"

    @staticmethod
    def _combined_market_bias(
        fii_net: float,
        dii_net: float,
    ) -> dict[str, str]:
        combined = fii_net + dii_net

        if fii_net > 0 and dii_net > 0:
            return {
                "market_bias": "BULLISH",
                "flow_structure": "BOTH_BUYING",
                "interpretation": (
                    "Foreign and domestic institutions are both net buyers."
                ),
            }

        if fii_net < 0 and dii_net < 0:
            return {
                "market_bias": "BEARISH",
                "flow_structure": "BOTH_SELLING",
                "interpretation": (
                    "Foreign and domestic institutions are both net sellers."
                ),
            }

        if fii_net < 0 < dii_net:
            if combined > 0:
                bias = "DOMESTICALLY_SUPPORTED"
            elif combined < 0:
                bias = "FII_SELLING_DOMINANT"
            else:
                bias = "BALANCED"

            return {
                "market_bias": bias,
                "flow_structure": "FII_SELL_DII_BUY",
                "interpretation": (
                    "Domestic buying is absorbing foreign institutional selling."
                ),
            }

        if fii_net > 0 > dii_net:
            if combined > 0:
                bias = "FII_BUYING_DOMINANT"
            elif combined < 0:
                bias = "DOMESTIC_SELLING_DOMINANT"
            else:
                bias = "BALANCED"

            return {
                "market_bias": bias,
                "flow_structure": "FII_BUY_DII_SELL",
                "interpretation": (
                    "Foreign buying is offset by domestic institutional selling."
                ),
            }

        if combined > 0:
            bias = "MILD_BULLISH"
        elif combined < 0:
            bias = "MILD_BEARISH"
        else:
            bias = "NEUTRAL"

        return {
            "market_bias": bias,
            "flow_structure": "MIXED",
            "interpretation": (
                "Institutional flows are mixed or limited."
            ),
        }

    def _validate_payload(
        self,
        payload: dict[str, Any],
    ) -> None:
        if not isinstance(payload, dict):
            raise FIIDIIEngineError(
                "FII/DII payload must be a dictionary."
            )

        if payload.get("data_status") == "NO_DATA":
            raise FIIDIIEngineError(
                "FII/DII analysis blocked because data status is NO_DATA."
            )

        if not isinstance(payload.get("fii"), dict):
            raise FIIDIIEngineError(
                "Missing or invalid FII section."
            )

        if not isinstance(payload.get("dii"), dict):
            raise FIIDIIEngineError(
                "Missing or invalid DII section."
            )

    def analyse(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._validate_payload(payload)

        fii = payload["fii"]
        dii = payload["dii"]

        fii_cash_buy = self._number(
            fii.get("cash_buy")
        )
        fii_cash_sell = self._number(
            fii.get("cash_sell")
        )
        fii_cash_net = round(
            fii_cash_buy - fii_cash_sell,
            4,
        )

        dii_cash_buy = self._number(
            dii.get("cash_buy")
        )
        dii_cash_sell = self._number(
            dii.get("cash_sell")
        )
        dii_cash_net = round(
            dii_cash_buy - dii_cash_sell,
            4,
        )

        fii_index_futures_net = self._number(
            fii.get("index_futures_net")
        )
        fii_stock_futures_net = self._number(
            fii.get("stock_futures_net")
        )
        fii_index_options_net = self._number(
            fii.get("index_options_net")
        )

        fii_derivatives_net = round(
            fii_index_futures_net
            + fii_stock_futures_net
            + fii_index_options_net,
            4,
        )

        fii_combined_net = round(
            fii_cash_net + fii_derivatives_net,
            4,
        )

        combined_cash_net = round(
            fii_cash_net + dii_cash_net,
            4,
        )

        flow_bias = self._combined_market_bias(
            fii_cash_net,
            dii_cash_net,
        )

        data_status = payload.get(
            "data_status",
            "UNKNOWN",
        )

        if data_status == "LIVE":
            confidence = "HIGH"
        elif data_status == "STALE":
            confidence = "LOW"
        else:
            confidence = "MEDIUM"

        participant_table = [
            {
                "participant": "FII",
                "position": self._position(
                    fii_cash_net
                ),
                "amount": fii_cash_net,
                "impact": self._impact(
                    "FII",
                    fii_cash_net,
                ),
            },
            {
                "participant": "DII",
                "position": self._position(
                    dii_cash_net
                ),
                "amount": dii_cash_net,
                "impact": self._impact(
                    "DII",
                    dii_cash_net,
                ),
            },
        ]

        return {
            "source": payload.get("source"),
            "source_confidence": self._number(
                payload.get("source_confidence")
            ),
            "data_status": data_status,
            "trade_date": payload.get("trade_date"),
            "timestamp": payload.get(
                "timestamp",
                datetime.now().astimezone().isoformat(),
            ),
            "participant_table": participant_table,
            "fii": {
                "cash_buy": fii_cash_buy,
                "cash_sell": fii_cash_sell,
                "cash_net": fii_cash_net,
                "index_futures_net": (
                    fii_index_futures_net
                ),
                "stock_futures_net": (
                    fii_stock_futures_net
                ),
                "index_options_net": (
                    fii_index_options_net
                ),
                "derivatives_net": (
                    fii_derivatives_net
                ),
                "combined_net": fii_combined_net,
                "position": self._position(
                    fii_combined_net
                ),
            },
            "dii": {
                "cash_buy": dii_cash_buy,
                "cash_sell": dii_cash_sell,
                "cash_net": dii_cash_net,
                "position": self._position(
                    dii_cash_net
                ),
            },
            "combined_cash_net": combined_cash_net,
            "market_bias": flow_bias[
                "market_bias"
            ],
            "flow_structure": flow_bias[
                "flow_structure"
            ],
            "interpretation": flow_bias[
                "interpretation"
            ],
            "confidence": confidence,
            "risk_note": (
                "Institutional flow data represents reported positioning "
                "and must not be treated as a standalone prediction."
            ),
        }


if __name__ == "__main__":
    sample_payload = {
        "source": "TEST_FIXTURE",
        "source_confidence": 100,
        "data_status": "LIVE",
        "trade_date": "2026-07-11",
        "fii": {
            "cash_buy": 12500,
            "cash_sell": 13800,
            "index_futures_net": -750,
            "stock_futures_net": 420,
            "index_options_net": -300,
        },
        "dii": {
            "cash_buy": 11200,
            "cash_sell": 9600,
        },
    }

    result = FIIDIIEngine().analyse(
        sample_payload
    )

    print("=" * 60)
    print("TRINETRA - FII/DII INTELLIGENCE")
    print("=" * 60)

    for row in result["participant_table"]:
        print(
            f"{row['participant']}: "
            f"{row['position']} | "
            f"₹{row['amount']} Cr | "
            f"{row['impact']}"
        )

    print(
        f"Combined Cash Net : "
        f"₹{result['combined_cash_net']} Cr"
    )
    print(
        f"Market Bias       : "
        f"{result['market_bias']}"
    )
    print(
        f"Flow Structure    : "
        f"{result['flow_structure']}"
    )
    print(
        f"Confidence        : "
        f"{result['confidence']}"
    )
