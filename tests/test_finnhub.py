from src.connectors.finnhub_connector import get_quote
from src.core.normalizer import normalize_finnhub_quote


raw_quote = get_quote("AAPL")

market_data = normalize_finnhub_quote(
    name="Apple",
    symbol="AAPL",
    asset_class="equity",
    raw_data=raw_quote,
)

print("=" * 55)
print("TRINETRA - FINNHUB TEST")
print("=" * 55)
print("Symbol      :", market_data.symbol)
print("Current     :", market_data.detailed_price())
print("Compact     :", market_data.compact_price())
print("Previous    :", market_data.previous_close)
print("Open        :", market_data.open)
print("High        :", market_data.high)
print("Low         :", market_data.low)
print("Change      :", market_data.change)
print("Change %    :", market_data.change_percent)
print("Source      :", market_data.source)
print("Confidence  :", market_data.confidence)
