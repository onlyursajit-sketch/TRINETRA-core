from __future__ import annotations

from src.intelligence.demand_supply_zones import (
    DemandSupplyZoneEngine,
)


def test_maps_demand_zone_from_bullish_base() -> None:
    result = DemandSupplyZoneEngine().map_zone(
        open_price=100.0,
        high=102.0,
        low=98.0,
        close=101.5,
        breakout_close=105.0,
    )

    assert result.zone_type == "DEMAND"
    assert result.lower_bound == 98.0
    assert result.upper_bound == 102.0


def test_maps_supply_zone_from_bearish_base() -> None:
    result = DemandSupplyZoneEngine().map_zone(
        open_price=100.0,
        high=103.0,
        low=99.0,
        close=99.5,
        breakout_close=96.0,
    )

    assert result.zone_type == "SUPPLY"
    assert result.lower_bound == 99.0
    assert result.upper_bound == 103.0


def test_returns_neutral_when_no_clear_departure() -> None:
    result = DemandSupplyZoneEngine().map_zone(
        open_price=100.0,
        high=102.0,
        low=98.0,
        close=100.5,
        breakout_close=101.0,
    )

    assert result.zone_type == "NEUTRAL"
