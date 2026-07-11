from src.models.market_data import MarketData


def normalize_yahoo_quote(
    name: str,
    asset_class: str,
    raw_data: dict,
) -> MarketData:
    """Convert Yahoo connector output into TRINETRA MarketData."""

    return MarketData(
        symbol=str(raw_data.get("symbol", "")),
        display_name=name,
        asset_class=asset_class,
        exchange=raw_data.get("exchange"),
        currency=raw_data.get("currency"),
        previous_close=raw_data.get("previous_close"),
        open=raw_data.get("open"),
        high=raw_data.get("high"),
        low=raw_data.get("low"),
        current=raw_data.get("current"),
        change=raw_data.get("change"),
        change_percent=raw_data.get("change_percent"),
        volume=raw_data.get("volume"),
        timestamp=raw_data.get("source_timestamp"),
        market_state=str(
            raw_data.get("market_state", "UNKNOWN")
        ),
        source=str(raw_data.get("source", "Yahoo")),
        data_state=str(
            raw_data.get("state", "estimated")
        ),
        confidence=75,
    )
def _to_float(value):
    if value in (None, ""):
        return None

    try:
        cleaned = str(value).replace("%", "").strip()
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    number = _to_float(value)

    if number is None:
        return None

    return int(number)


def normalize_alpha_quote(
    name: str,
    asset_class: str,
    raw_data: dict,
) -> MarketData:
    current = _to_float(raw_data.get("05. price"))
    previous = _to_float(raw_data.get("08. previous close"))
    change = _to_float(raw_data.get("09. change"))
    change_percent = _to_float(
        raw_data.get("10. change percent")
    )

    return MarketData(
        symbol=str(raw_data.get("01. symbol", "")),
        display_name=name,
        asset_class=asset_class,
        exchange=None,
        currency=None,
        previous_close=previous,
        open=_to_float(raw_data.get("02. open")),
        high=_to_float(raw_data.get("03. high")),
        low=_to_float(raw_data.get("04. low")),
        current=current,
        change=change,
        change_percent=change_percent,
        volume=_to_int(raw_data.get("06. volume")),
        timestamp=raw_data.get("07. latest trading day"),
        market_state="UNKNOWN",
        source="AlphaVantage",
        data_state="estimated",
        confidence=80,
    )
def normalize_finnhub_quote(
    name: str,
    symbol: str,
    asset_class: str,
    raw_data: dict,
) -> MarketData:
    current = _to_float(raw_data.get("c"))
    previous = _to_float(raw_data.get("pc"))
    change = _to_float(raw_data.get("d"))
    change_percent = _to_float(raw_data.get("dp"))

    timestamp_value = raw_data.get("t")

    timestamp = (
        str(timestamp_value)
        if timestamp_value
        else None
    )

    return MarketData(
        symbol=symbol,
        display_name=name,
        asset_class=asset_class,
        exchange=None,
        currency="USD",
        previous_close=previous,
        open=_to_float(raw_data.get("o")),
        high=_to_float(raw_data.get("h")),
        low=_to_float(raw_data.get("l")),
        current=current,
        change=change,
        change_percent=change_percent,
        volume=None,
        timestamp=timestamp,
        market_state="UNKNOWN",
        source="Finnhub",
        data_state="estimated",
        confidence=85,
    )
