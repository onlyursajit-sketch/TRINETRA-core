from src.connectors.yahoo_connector import get_quote
from src.core.normalizer import normalize_yahoo_quote


raw_quote = get_quote("^NSEI")

market_data = normalize_yahoo_quote(
    name="NIFTY 50",
    asset_class="index",
    raw_data=raw_quote,
)

print("=" * 50)
print("TRINETRA UNIVERSAL DATA MODEL TEST")
print("=" * 50)

print("Symbol         :", market_data.symbol)
print("Name           :", market_data.display_name)
print("Asset Class    :", market_data.asset_class)
print("Current Exact  :", market_data.detailed_price())
print("Current Compact:", market_data.compact_price())
print("Change %       :", market_data.change_percent)
print("Source         :", market_data.source)
print("Confidence     :", market_data.confidence)
print("Dictionary     :", market_data.to_dict())
