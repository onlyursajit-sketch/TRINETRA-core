import requests


def get_quote(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    response = requests.get(
        url,
        headers={"User-Agent": "TRINETRA/0.1"},
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    chart = data["chart"]["result"][0]
    meta = chart["meta"]

    return {
        "symbol": meta.get("symbol"),
        "exchange": meta.get("exchangeName"),
        "currency": meta.get("currency"),
        "previous_close": meta.get("chartPreviousClose"),
        "regular_market_price": meta.get("regularMarketPrice"),
        "high": meta.get("regularMarketDayHigh"),
        "low": meta.get("regularMarketDayLow"),
        "source": "Yahoo Finance",
    }
