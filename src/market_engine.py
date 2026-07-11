from src.connectors.yahoo_connector import get_quote
from src.core.normalizer import normalize_yahoo_quote


MARKET_SYMBOLS = {
    "NIFTY": {
        "symbol": "^NSEI",
        "asset_class": "index",
    },
    "BANKNIFTY": {
        "symbol": "^NSEBANK",
        "asset_class": "index",
    },
    "SENSEX": {
        "symbol": "^BSESN",
        "asset_class": "index",
    },
    "USDINR": {
        "symbol": "INR=X",
        "asset_class": "forex",
    },
    "GOLD": {
        "symbol": "GC=F",
        "asset_class": "commodity",
    },
    "SILVER": {
        "symbol": "SI=F",
        "asset_class": "commodity",
    },
    "CRUDE": {
        "symbol": "CL=F",
        "asset_class": "commodity",
    },
}


def get_market_snapshot():
    market = {}

    for name, config in MARKET_SYMBOLS.items():
        symbol = config["symbol"]
        asset_class = config["asset_class"]

        try:
            raw_data = get_quote(symbol)

            market[name] = normalize_yahoo_quote(
                name=name,
                asset_class=asset_class,
                raw_data=raw_data,
            )

        except Exception as exc:
            market[name] = {
                "error": str(exc),
                "symbol": symbol,
            }

    return market
