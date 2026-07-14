from src.connectors.alpha_vantage_connector import (
    get_global_quote,
)
from src.core.normalizer import normalize_alpha_quote


raw_quote = get_global_quote("IBM")

market_data = normalize_alpha_quote(
    name="IBM",
    asset_class="equity",
    raw_data=raw_quote,
)

print("=" * 55)
print("TRINETRA - ALPHA VANTAGE TEST")
print("=" * 55)
print("Symbol      :", market_data.symbol)
print("Current     :", market_data.detailed_price())
print("Compact     :", market_data.compact_price())
print("Previous    :", market_data.previous_close)
print("Open        :", market_data.open)
print("High        :", market_data.high)
print("Low         :", market_data.low)
print("Change %    :", market_data.change_percent)
print("Volume      :", market_data.volume)
print("Source      :", market_data.source)
print("Confidence  :", market_data.confidence)
