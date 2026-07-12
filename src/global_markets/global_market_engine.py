from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


class GlobalMarketEngineError(Exception):
    """Raised when global market data cannot be normalized."""


@dataclass(frozen=True)
class MarketDefinition:
    market_id: str
    country: str
    name: str
    provider_symbol: str
    timezone: str
    trading_hours: str
    asset_type: str = "INDEX"


class GlobalMarketEngine:
    """
    TRINETRA Global Market Intelligence Engine.

    Part 1 responsibilities:
    - Canonical global-market registry
    - Input validation
    - Numeric normalization
    - Previous → Current → Difference → Percentage
    - LIVE / STALE / NO_DATA handling
    - Source-confidence preservation

    No fabricated values are generated.
    """

    VALID_DATA_STATUSES = {
        "LIVE",
        "STALE",
        "NO_DATA",
        "PARTIAL",
        "UNKNOWN",
    }

    VALID_MARKET_STATUSES = {
        "OPEN",
        "CLOSED",
        "PRE_MARKET",
        "POST_MARKET",
        "HOLIDAY",
        "UNKNOWN",
    }

    MARKET_REGISTRY: dict[str, MarketDefinition] = {
        "DOW_JONES": MarketDefinition(
            market_id="DOW_JONES",
            country="USA",
            name="Dow Jones",
            provider_symbol="^DJI",
            timezone="America/New_York",
            trading_hours="09:30-16:00",
        ),
        "SP500": MarketDefinition(
            market_id="SP500",
            country="USA",
            name="S&P 500",
            provider_symbol="^GSPC",
            timezone="America/New_York",
            trading_hours="09:30-16:00",
        ),
        "NASDAQ": MarketDefinition(
            market_id="NASDAQ",
            country="USA",
            name="Nasdaq Composite",
            provider_symbol="^IXIC",
            timezone="America/New_York",
            trading_hours="09:30-16:00",
        ),
        "TSX": MarketDefinition(
            market_id="TSX",
            country="Canada",
            name="S&P/TSX Composite",
            provider_symbol="^GSPTSE",
            timezone="America/Toronto",
            trading_hours="09:30-16:00",
        ),
        "FTSE100": MarketDefinition(
            market_id="FTSE100",
            country="UK",
            name="FTSE 100",
            provider_symbol="^FTSE",
            timezone="Europe/London",
            trading_hours="08:00-16:30",
        ),
        "DAX": MarketDefinition(
            market_id="DAX",
            country="Germany",
            name="DAX",
            provider_symbol="^GDAXI",
            timezone="Europe/Berlin",
            trading_hours="09:00-17:30",
        ),
        "CAC40": MarketDefinition(
            market_id="CAC40",
            country="France",
            name="CAC 40",
            provider_symbol="^FCHI",
            timezone="Europe/Paris",
            trading_hours="09:00-17:30",
        ),
        "NIKKEI225": MarketDefinition(
            market_id="NIKKEI225",
            country="Japan",
            name="Nikkei 225",
            provider_symbol="^N225",
            timezone="Asia/Tokyo",
            trading_hours="09:00-15:30",
        ),
        "SHANGHAI": MarketDefinition(
            market_id="SHANGHAI",
            country="China",
            name="Shanghai Composite",
            provider_symbol="000001.SS",
            timezone="Asia/Shanghai",
            trading_hours="09:30-15:00",
        ),
        "HANG_SENG": MarketDefinition(
            market_id="HANG_SENG",
            country="Hong Kong",
            name="Hang Seng",
            provider_symbol="^HSI",
            timezone="Asia/Hong_Kong",
            trading_hours="09:30-16:00",
        ),
        "KOSPI": MarketDefinition(
            market_id="KOSPI",
            country="South Korea",
            name="KOSPI",
            provider_symbol="^KS11",
            timezone="Asia/Seoul",
            trading_hours="09:00-15:30",
        ),
        "TAIEX": MarketDefinition(
            market_id="TAIEX",
            country="Taiwan",
            name="TAIEX",
            provider_symbol="^TWII",
            timezone="Asia/Taipei",
            trading_hours="09:00-13:30",
        ),
        "STI": MarketDefinition(
            market_id="STI",
            country="Singapore",
            name="Straits Times",
            provider_symbol="^STI",
            timezone="Asia/Singapore",
            trading_hours="09:00-17:00",
        ),
        "ASX200": MarketDefinition(
            market_id="ASX200",
            country="Australia",
            name="S&P/ASX 200",
            provider_symbol="^AXJO",
            timezone="Australia/Sydney",
            trading_hours="10:00-16:00",
        ),
        "IBOVESPA": MarketDefinition(
            market_id="IBOVESPA",
            country="Brazil",
            name="Bovespa",
            provider_symbol="^BVSP",
            timezone="America/Sao_Paulo",
            trading_hours="10:00-17:00",
        ),
        "MOEX": MarketDefinition(
            market_id="MOEX",
            country="Russia",
            name="MOEX Russia",
            provider_symbol="IMOEX.ME",
            timezone="Europe/Moscow",
            trading_hours="10:00-18:50",
        ),
        "GIFT_NIFTY": MarketDefinition(
            market_id="GIFT_NIFTY",
            country="India",
            name="GIFT Nifty",
            provider_symbol="GIFT_NIFTY",
            timezone="Asia/Kolkata",
            trading_hours="06:30-02:45",
            asset_type="FUTURE",
        ),
        "DOW_FUTURES": MarketDefinition(
            market_id="DOW_FUTURES",
            country="USA",
            name="Dow Futures",
            provider_symbol="YM=F",
            timezone="America/New_York",
            trading_hours="Nearly 24 Hours",
            asset_type="FUTURE",
        ),
    }

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _number(
        value: Any,
    ) -> float | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _text(
        value: Any,
        default: str = "N/A",
    ) -> str:
        if value is None:
            return default

        cleaned = str(value).strip()
        return cleaned or default

    @classmethod
    def _normalize_data_status(
        cls,
        value: Any,
    ) -> str:
        if not isinstance(value, str):
            return "UNKNOWN"

        status = value.strip().upper()

        if status not in cls.VALID_DATA_STATUSES:
            return "UNKNOWN"

        return status

    @classmethod
    def _normalize_market_status(
        cls,
        value: Any,
    ) -> str:
        if not isinstance(value, str):
            return "UNKNOWN"

        status = value.strip().upper()

        if status not in cls.VALID_MARKET_STATUSES:
            return "UNKNOWN"

        return status

    @staticmethod
    def _normalize_confidence(
        value: Any,
    ) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.0

        return round(
            max(0.0, min(100.0, confidence)),
            2,
        )

    @classmethod
    def get_definition(
        cls,
        market_id: str,
    ) -> MarketDefinition:
        clean_id = market_id.strip().upper()

        definition = cls.MARKET_REGISTRY.get(
            clean_id
        )

        if definition is None:
            raise GlobalMarketEngineError(
                f"Unsupported global market: {clean_id}"
            )

        return definition

    def normalize_quote(
        self,
        market_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise GlobalMarketEngineError(
                "Global market payload must be a dictionary."
            )

        definition = self.get_definition(
            market_id
        )

        previous = self._number(
            payload.get("previous_close")
        )
        current = self._number(
            payload.get("current")
        )

        open_value = self._number(
            payload.get("open")
        )
        high = self._number(
            payload.get("high")
        )
        low = self._number(
            payload.get("low")
        )

        difference = None
        percentage_change = None

        if previous is not None and current is not None:
            difference = round(
                current - previous,
                4,
            )

            if previous != 0:
                percentage_change = round(
                    (difference / previous) * 100,
                    4,
                )

        data_status = self._normalize_data_status(
            payload.get("data_status")
        )

        if previous is None or current is None:
            data_status = "NO_DATA"

        return {
            **asdict(definition),
            "previous_close": previous,
            "open": open_value,
            "high": high,
            "low": low,
            "current": current,
            "difference": difference,
            "percentage_change": percentage_change,
            "local_time": self._text(
                payload.get("local_time")
            ),
            "market_status": self._normalize_market_status(
                payload.get("market_status")
            ),
            "why_moving": self._text(
                payload.get("why_moving"),
                "Reason not verified.",
            ),
            "source": self._text(
                payload.get("source")
            ),
            "source_confidence": (
                self._normalize_confidence(
                    payload.get("source_confidence")
                )
            ),
            "data_status": data_status,
            "timestamp": self._text(
                payload.get("timestamp"),
                self._utc_now(),
            ),
        }



    def build_snapshot(
        self,
        payloads: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        markets: list[dict[str, Any]] = []

        advances = 0
        declines = 0
        unchanged = 0

        live = 0
        stale = 0
        no_data = 0

        for market_id, payload in payloads.items():
            quote = self.normalize_quote(
                market_id,
                payload,
            )

            markets.append(quote)

            change = quote["difference"]

            if change is None:
                pass
            elif change > 0:
                advances += 1
            elif change < 0:
                declines += 1
            else:
                unchanged += 1

            status = quote["data_status"]

            if status == "LIVE":
                live += 1
            elif status == "STALE":
                stale += 1
            else:
                no_data += 1

        total = len(markets)

        if total == 0 or no_data == total:
            health = "NO_DATA"
        elif live == total:
            health = "LIVE"
        else:
            health = "PARTIAL"

        return {
            "generated_at": self._utc_now(),
            "health": health,
            "summary": {
                "total_markets": total,
                "advances": advances,
                "declines": declines,
                "unchanged": unchanged,
                "live": live,
                "stale": stale,
                "no_data": no_data,
            },
            "markets": markets,
        }

if __name__ == "__main__":
    engine = GlobalMarketEngine()

    sample = engine.normalize_quote(
        "DOW_JONES",
        {
            "previous_close": 45000,
            "open": 45050,
            "high": 45200,
            "low": 44900,
            "current": 45150,
            "local_time": "13:30",
            "market_status": "OPEN",
            "why_moving": "Test fixture only.",
            "source": "TEST_FIXTURE",
            "source_confidence": 100,
            "data_status": "LIVE",
        },
    )

    print("=" * 68)
    print("TRINETRA - GLOBAL MARKET ENGINE")
    print("=" * 68)

    for key, value in sample.items():
        print(f"{key}: {value}")
