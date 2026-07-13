from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    capital: float
    risk_per_trade_pct: float = 1.0
    max_position_pct: float = 20.0
    min_risk_reward: float = 2.0
