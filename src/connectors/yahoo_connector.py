from datetime import datetime, timezone

import requests


YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def get_quote(symbol):
    url = YAHOO_URL.format(symbol=symbol)

    response = requests.get(
        url,
        params={
            "interval": "1m",
            "range": "1d",
            "includePrePost": "false",
        },
        headers={
            "User-Agent": "Mozilla/5.0 TRINETRA/0.5",
            "Accept": "application/json",
        },
        timeout=15,
    )

    response.raise_for_status()
    payload = response.json()

    chart = payload.get("chart", {})

    if chart.get("error"):
        raise RuntimeError(str(chart["error"]))

    results = chart.get("result") or []

    if not results:
        raise RuntimeError(f"No Yahoo data returned for {symbol}")

    result = results[0]
    meta = result.get("meta", {})

    current = meta.get("regularMarketPrice")
    previous = (
        meta.get("chartPreviousClose")
        or meta.get("previousClose")
    )

    change = None
    change_percent = None

    if current is not None and previous not in (None, 0):
        change = current - previous
        change_percent = (change / previous) * 100

    market_timestamp = meta.get("regularMarketTime")

    if market_timestamp:
        source_timestamp = datetime.fromtimestamp(
            market_timestamp,
            tz=timezone.utc,
        ).isoformat()
    else:
        source_timestamp = None

    return {
        "symbol": meta.get("symbol", symbol),
        "display_name": (
            meta.get("longName")
            or meta.get("shortName")
            or symbol
        ),
        "exchange": meta.get("exchangeName"),
        "currency": meta.get("currency"),
        "previous_close": previous,
        "open": meta.get("regularMarketOpen"),
        "high": meta.get("regularMarketDayHigh"),
        "low": meta.get("regularMarketDayLow"),
        "current": current,
        "change": change,
        "change_percent": change_percent,
        "market_state": meta.get("marketState", "UNKNOWN"),
        "source_timestamp": source_timestamp,
        "source": "Yahoo",
        "state": "estimated",
    }
