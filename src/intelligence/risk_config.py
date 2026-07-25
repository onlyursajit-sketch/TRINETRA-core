from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    capital: float
    risk_per_trade_pct: float = 1.0
    max_position_pct: float = 20.0
    min_risk_reward: float = 2.0

    def __post_init__(self) -> None:
        if self.capital <= 0:
            raise ValueError(
                "Capital must be greater than zero"
            )

        if not 0 < self.risk_per_trade_pct <= 100:
            raise ValueError(
                "Risk per trade percentage must be between 0 and 100"
            )
