from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class RiskConfig:
    capital: float
    risk_per_trade_pct: float = 1.0
    max_position_pct: float = 20.0
    min_risk_reward: float = 2.0

    def __post_init__(self) -> None:
        values = (
            self.capital,
            self.risk_per_trade_pct,
            self.max_position_pct,
            self.min_risk_reward,
        )

        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            for value in values
        ):
            raise ValueError(
                "Risk configuration values must be numeric"
            )

        if not all(
            isfinite(value)
            for value in values
        ):
            raise ValueError(
                "Risk configuration values must be finite numbers"
            )

        if self.capital <= 0:
            raise ValueError(
                "Capital must be greater than zero"
            )

        if not 0 < self.risk_per_trade_pct <= 100:
            raise ValueError(
                "Risk per trade percentage must be between 0 and 100"
            )

        if not 0 < self.max_position_pct <= 100:
            raise ValueError(
                "Maximum position percentage must be between 0 and 100"
            )

        if self.min_risk_reward <= 0:
            raise ValueError(
                "Minimum risk-reward must be greater than zero"
            )
