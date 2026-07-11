from src.connectors.alpha_vantage_connector import (
    get_global_quote,
)
from src.connectors.finnhub_connector import (
    get_quote as get_finnhub_quote,
)
from src.connectors.yahoo_connector import (
    get_quote as get_yahoo_quote,
)
from src.core.normalizer import (
    normalize_alpha_quote,
    normalize_finnhub_quote,
    normalize_yahoo_quote,
)
from src.core.source_manager import fetch_with_fallback


def get_us_equity(
    symbol: str,
    name: str,
):
    def fetch_finnhub():
        raw_data = get_finnhub_quote(symbol)

        return normalize_finnhub_quote(
            name=name,
            symbol=symbol,
            asset_class="equity",
            raw_data=raw_data,
        )

    def fetch_alpha_vantage():
        raw_data = get_global_quote(symbol)

        return normalize_alpha_quote(
            name=name,
            asset_class="equity",
            raw_data=raw_data,
        )

    def fetch_yahoo():
        raw_data = get_yahoo_quote(symbol)

        return normalize_yahoo_quote(
            name=name,
            asset_class="equity",
            raw_data=raw_data,
        )

    data, errors = fetch_with_fallback(
        {
            "Finnhub": fetch_finnhub,
            "AlphaVantage": fetch_alpha_vantage,
            "Yahoo": fetch_yahoo,
        }
    )

    return data, errors
