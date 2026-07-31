from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HigherTimeframeTrendResult:
    trend: str
    higher_highs: bool
    higher_lows: bool
    lower_highs: bool
    lower_lows: bool


class HigherTimeframeTrendEngine:
    """Classifies market structure from higher-timeframe swing highs/lows."""

    def classify(
        self,
        highs: list[float],
        lows: list[float],
    ) -> HigherTimeframeTrendResult:
        if len(highs) < 2 or len(lows) < 2:
            raise ValueError(
                "At least two highs and two lows are required"
            )

        if len(highs) != len(lows):
            raise ValueError(
                "Highs and lows must contain the same number of values"
            )

        higher_highs = all(
            current > previous
            for previous, current in zip(highs, highs[1:])
        )
        higher_lows = all(
            current > previous
            for previous, current in zip(lows, lows[1:])
        )
        lower_highs = all(
            current < previous
            for previous, current in zip(highs, highs[1:])
        )
        lower_lows = all(
            current < previous
            for previous, current in zip(lows, lows[1:])
        )

        if higher_highs and higher_lows:
            trend = "BULLISH"
        elif lower_highs and lower_lows:
            trend = "BEARISH"
        else:
            trend = "RANGE"

        return HigherTimeframeTrendResult(
            trend=trend,
            higher_highs=higher_highs,
            higher_lows=higher_lows,
            lower_highs=lower_highs,
            lower_lows=lower_lows,
        )
