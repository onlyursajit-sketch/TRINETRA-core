from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemandSupplyZoneResult:
    zone_type: str
    lower_bound: float
    upper_bound: float


class DemandSupplyZoneEngine:
    """Maps a simple demand/supply zone from a base candle and departure."""

    def map_zone(
        self,
        open_price: float,
        high: float,
        low: float,
        close: float,
        breakout_close: float,
    ) -> DemandSupplyZoneResult:
        if low > high:
            raise ValueError("Low price cannot exceed high price")

        bullish_base = close >= open_price
        bearish_base = close < open_price

        clear_bullish_departure = breakout_close > high
        clear_bearish_departure = breakout_close < low

        if bullish_base and clear_bullish_departure:
            zone_type = "DEMAND"
        elif bearish_base and clear_bearish_departure:
            zone_type = "SUPPLY"
        else:
            zone_type = "NEUTRAL"

        return DemandSupplyZoneResult(
            zone_type=zone_type,
            lower_bound=low,
            upper_bound=high,
        )
