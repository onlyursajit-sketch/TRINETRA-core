from __future__ import annotations

from typing import Any, Callable

from src.connectors.yahoo_connector import get_quote


class IndiaVIXCollectorError(Exception):
    """Raised when India VIX market data cannot be collected."""


class IndiaVIXCollector:
    YAHOO_SYMBOL = "^INDIAVIX"

    def __init__(
        self,
        fetcher: Callable[[str], dict[str, Any]] = get_quote,
    ) -> None:
        self.fetcher = fetcher

    def collect(self) -> dict[str, Any]:
        try:
            quote = self.fetcher(self.YAHOO_SYMBOL)
        except Exception as exc:
            raise IndiaVIXCollectorError(
                f"Failed to collect India VIX: {exc}"
            ) from exc

        if not isinstance(quote, dict):
            raise IndiaVIXCollectorError(
                "India VIX provider returned invalid payload."
            )

        current = quote.get("current")
        previous_close = quote.get("previous_close")

        if not isinstance(current, (int, float)) or isinstance(current, bool):
            raise IndiaVIXCollectorError(
                "India VIX current value is missing or invalid."
            )

        return {
            "symbol": "INDIA_VIX",
            "previous_close": previous_close,
            "open": quote.get("open"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "current": current,
            "timestamp": quote.get("source_timestamp"),
            "source": quote.get("source", "Yahoo"),
            "data_status": "STALE",
            "source_confidence": 70,
        }
