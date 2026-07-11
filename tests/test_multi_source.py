from src.multi_source_engine import get_us_equity


print("=" * 60)
print("TRINETRA - MULTI SOURCE FALLBACK TEST")
print("=" * 60)

market_data, errors = get_us_equity(
    symbol="AAPL",
    name="Apple",
)

if market_data is None:
    print("Result : FAILED")

    for error in errors:
        print("Error  :", error)

else:
    print("Result     : SUCCESS")
    print("Symbol     :", market_data.symbol)
    print("Current    :", market_data.detailed_price())
    print("Previous   :", market_data.previous_close)
    print("Open       :", market_data.open)
    print("High       :", market_data.high)
    print("Low        :", market_data.low)
    print("Change %   :", market_data.change_percent)
    print("Source     :", market_data.source)
    print("Confidence :", market_data.confidence)

    if errors:
        print()
        print("Failed sources before success:")

        for error in errors:
            print("-", error)
