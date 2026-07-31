from __future__ import annotations

from src.intelligence.higher_timeframe_trend import (
    HigherTimeframeTrendEngine,
)


def test_higher_timeframe_trend_classifies_bullish_structure() -> None:
    result = HigherTimeframeTrendEngine().classify(
        highs=[100.0, 105.0, 110.0],
        lows=[90.0, 95.0, 100.0],
    )

    assert result.trend == "BULLISH"
    assert result.higher_highs is True
    assert result.higher_lows is True


def test_higher_timeframe_trend_classifies_bearish_structure() -> None:
    result = HigherTimeframeTrendEngine().classify(
        highs=[110.0, 105.0, 100.0],
        lows=[100.0, 95.0, 90.0],
    )

    assert result.trend == "BEARISH"
    assert result.lower_highs is True
    assert result.lower_lows is True


def test_higher_timeframe_trend_classifies_range() -> None:
    result = HigherTimeframeTrendEngine().classify(
        highs=[100.0, 101.0, 100.5],
        lows=[95.0, 94.5, 95.0],
    )

    assert result.trend == "RANGE"
