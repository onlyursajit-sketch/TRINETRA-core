from __future__ import annotations

from typing import Any

from src.global_markets.global_market_engine import (
    GlobalMarketEngine,
    GlobalMarketEngineError,
)


class GlobalCommandCenterError(Exception):
    """Raised when the Global Command Center cannot be built."""


class GlobalCommandCenter:
    """
    TRINETRA Global Command Center.

    Responsibilities:
    - Multiple global-market payloads process karna
    - Canonical ordering maintain karna
    - Global breadth calculate karna
    - LIVE / STALE / NO_DATA summary banana
    - Source confidence calculate karna
    - Deterministic global bias generate karna

    No fabricated market values are generated.
    """

    MARKET_ORDER = [
        "DOW_JONES",
        "SP500",
        "NASDAQ",
        "TSX",
        "FTSE100",
        "DAX",
        "CAC40",
        "NIKKEI225",
        "SHANGHAI",
        "HANG_SENG",
        "KOSPI",
        "TAIEX",
        "STI",
        "ASX200",
        "IBOVESPA",
        "MOEX",
        "GIFT_NIFTY",
        "DOW_FUTURES",
    ]

    def __init__(
        self,
        market_engine: GlobalMarketEngine | None = None,
    ) -> None:
        self.market_engine = (
            market_engine
            or GlobalMarketEngine()
        )

    @staticmethod
    def _average_confidence(
        markets: list[dict[str, Any]],
    ) -> float:
        values: list[float] = []

        for market in markets:
            value = market.get(
                "source_confidence"
            )

            if isinstance(value, (int, float)):
                if 0 <= float(value) <= 100:
                    values.append(
                        float(value)
                    )

        if not values:
            return 0.0

        return round(
            sum(values) / len(values),
            2,
        )

    @staticmethod
    def _global_bias(
        advances: int,
        declines: int,
        unchanged: int,
    ) -> str:
        total_directional = (
            advances + declines
        )

        if total_directional == 0:
            return "UNAVAILABLE"

        ratio = advances / total_directional

        if ratio >= 0.75:
            return "STRONG_BULLISH"

        if ratio >= 0.60:
            return "BULLISH"

        if ratio > 0.40:
            return "NEUTRAL"

        if ratio > 0.25:
            return "BEARISH"

        return "STRONG_BEARISH"

    @staticmethod
    def _warnings(
        summary: dict[str, Any],
        source_confidence: float,
    ) -> list[str]:
        warnings: list[str] = []

        if summary.get("no_data", 0) > 0:
            warnings.append(
                "GLOBAL_DATA_MISSING"
            )

        if summary.get("stale", 0) > 0:
            warnings.append(
                "GLOBAL_DATA_STALE"
            )

        if source_confidence < 60:
            warnings.append(
                "LOW_GLOBAL_SOURCE_CONFIDENCE"
            )

        if summary.get("total_markets", 0) == 0:
            warnings.append(
                "NO_GLOBAL_MARKETS_AVAILABLE"
            )

        return warnings

    def _ordered_payloads(
        self,
        payloads: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        ordered: dict[str, dict[str, Any]] = {}

        for market_id in self.MARKET_ORDER:
            if market_id in payloads:
                ordered[market_id] = payloads[
                    market_id
                ]

        for market_id, payload in payloads.items():
            if market_id not in ordered:
                ordered[market_id] = payload

        return ordered

    def build(
        self,
        payloads: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        if not isinstance(payloads, dict):
            raise GlobalCommandCenterError(
                "Global payloads must be a dictionary."
            )

        ordered_payloads = self._ordered_payloads(
            payloads
        )

        try:
            snapshot = (
                self.market_engine.build_snapshot(
                    ordered_payloads
                )
            )

        except GlobalMarketEngineError as exc:
            raise GlobalCommandCenterError(
                str(exc)
            ) from exc

        markets = snapshot.get(
            "markets",
            [],
        )

        summary = snapshot.get(
            "summary",
            {},
        )

        if not isinstance(markets, list):
            markets = []

        if not isinstance(summary, dict):
            summary = {}

        source_confidence = (
            self._average_confidence(
                markets
            )
        )

        global_bias = self._global_bias(
            int(summary.get("advances", 0)),
            int(summary.get("declines", 0)),
            int(summary.get("unchanged", 0)),
        )

        warnings = self._warnings(
            summary,
            source_confidence,
        )

        return {
            "command_center": (
                "TRINETRA_GLOBAL"
            ),
            "generated_at": snapshot.get(
                "generated_at"
            ),
            "health": snapshot.get(
                "health",
                "NO_DATA",
            ),
            "global_bias": global_bias,
            "source_confidence": (
                source_confidence
            ),
            "summary": summary,
            "markets": markets,
            "warnings": warnings,
        }


if __name__ == "__main__":
    engine = GlobalCommandCenter()

    fixture_payloads = {
        "DOW_JONES": {
            "previous_close": 45000,
            "open": 45050,
            "high": 45200,
            "low": 44900,
            "current": 45150,
            "local_time": "13:30",
            "market_status": "OPEN",
            "why_moving": (
                "Test fixture only."
            ),
            "source": "TEST_FIXTURE",
            "source_confidence": 100,
            "data_status": "LIVE",
        },
        "NASDAQ": {
            "previous_close": 20000,
            "open": 20020,
            "high": 20100,
            "low": 19850,
            "current": 19900,
            "local_time": "13:30",
            "market_status": "OPEN",
            "why_moving": (
                "Test fixture only."
            ),
            "source": "TEST_FIXTURE",
            "source_confidence": 100,
            "data_status": "LIVE",
        },
        "NIKKEI225": {
            "previous_close": 41000,
            "open": 41100,
            "high": 41300,
            "low": 40950,
            "current": 41200,
            "local_time": "15:00",
            "market_status": "CLOSED",
            "why_moving": (
                "Test fixture only."
            ),
            "source": "TEST_FIXTURE",
            "source_confidence": 100,
            "data_status": "LIVE",
        },
    }

    result = engine.build(
        fixture_payloads
    )

    print("=" * 70)
    print(
        "TRINETRA GLOBAL COMMAND CENTER"
    )
    print("=" * 70)
    print(
        f"Health             : "
        f"{result['health']}"
    )
    print(
        f"Global Bias        : "
        f"{result['global_bias']}"
    )
    print(
        f"Source Confidence  : "
        f"{result['source_confidence']}"
    )
    print(
        f"Summary            : "
        f"{result['summary']}"
    )
    print(
        f"Warnings           : "
        f"{result['warnings']}"
    )
