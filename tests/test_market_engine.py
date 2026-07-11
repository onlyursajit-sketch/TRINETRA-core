from src.market_engine import get_market_snapshot


print("=" * 60)
print("TRINETRA - UNIVERSAL MARKET ENGINE TEST")
print("=" * 60)

market = get_market_snapshot()

for name, data in market.items():
    print()

    if isinstance(data, dict) and "error" in data:
        print(f"{name:12}: ERROR")
        print(f"Reason      : {data['error']}")
        continue

    print(f"{name:12}: {data.compact_price()}")
    print(f"Exact       : {data.detailed_price()}")
    print(f"Previous    : {data.previous_close}")
    print(f"Open        : {data.open}")
    print(f"High        : {data.high}")
    print(f"Low         : {data.low}")
    print(f"Change %    : {data.change_percent}")
    print(f"Asset Class : {data.asset_class}")
    print(f"Source      : {data.source}")
    print(f"Confidence  : {data.confidence}")
