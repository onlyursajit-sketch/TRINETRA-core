from src.market_engine import get_market_snapshot

print("=" * 60)
print("TRINETRA - MULTI ASSET MARKET TEST")
print("=" * 60)

market = get_market_snapshot()

for name, data in market.items():
    print()

    if "error" in data:
        print(f"{name:12}: ERROR")
        print(f"Reason      : {data['error']}")
        continue

    print(f"{name:12}: {data.get('regular_market_price')}")
    print(f"Previous    : {data.get('previous_close')}")
    print(f"High        : {data.get('high')}")
    print(f"Low         : {data.get('low')}")
    print(f"Currency    : {data.get('currency')}")
    print(f"Source      : {data.get('source')}")
