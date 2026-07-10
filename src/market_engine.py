from src.connectors.yahoo_connector import get_quote

MARKET_SYMBOLS = {
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
    "USDINR": "INR=X",
    "GOLD": "GC=F",
    "SILVER": "SI=F",
    "CRUDE": "CL=F",
}

def get_market_snapshot():
    market = {}

    for name, symbol in MARKET_SYMBOLS.items():
        try:
            market[name] = get_quote(symbol)
        except Exception as exc:
            market[name] = {
                "error": str(exc),
                "symbol": symbol,
            }

    return market
