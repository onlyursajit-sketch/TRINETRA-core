from src.connectors.yahoo_connector import get_quote

print("=" * 50)
print("TRINETRA - YAHOO MARKET TEST")
print("=" * 50)

quote = get_quote("^NSEI")

print()
print("Market Data")
print("-" * 50)

for key, value in quote.items():
    print(f"{key:25}: {value}")
