from src.core.source_manager import (
    fetch_with_fallback,
    rank_sources,
)
from src.models.market_data import MarketData


def failing_yahoo() -> MarketData:
    raise RuntimeError("Yahoo unavailable")


def working_alpha() -> MarketData:
    return MarketData(
        symbol="TEST",
        display_name="Test Asset",
        asset_class="index",
        exchange="TEST",
        currency="INR",
        previous_close=100.0,
        open=101.0,
        high=105.0,
        low=99.0,
        current=104.0,
        change=4.0,
        change_percent=4.0,
        volume=1000,
        timestamp="2026-07-11T09:00:00+05:30",
        market_state="OPEN",
        source="AlphaVantage",
        data_state="verified",
        confidence=80,
    )


print("=" * 60)
print("TRINETRA SOURCE MANAGER TEST")
print("=" * 60)

print(
    "Priority:",
    rank_sources(
        ["Yahoo", "AlphaVantage", "Dhan"]
    ),
)

data, errors = fetch_with_fallback(
    {
        "Yahoo": failing_yahoo,
        "AlphaVantage": working_alpha,
    }
)

print("Errors:", errors)

if data is None:
    print("Result: FAILED")
else:
    print("Result: SUCCESS")
    print("Source:", data.source)
    print("Price :", data.detailed_price())
