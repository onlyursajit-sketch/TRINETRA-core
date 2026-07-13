from __future__ import annotations

from dataclasses import dataclass

from src.intelligence.risk_config import RiskConfig


@dataclass(frozen=True)
class PositionResult:
    quantity: int
    capital_at_risk: float
    position_value: float
    stop_loss: float
    target: float
    risk_reward: float


class PositionSizer:
    """Calculates position size based on risk."""

    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def calculate(
        self,
        entry: float,
        stop_loss: float,
        target: float,
    ) -> PositionResult:

        risk_per_share = abs(entry - stop_loss)

        if risk_per_share <= 0:
            raise ValueError("Invalid stop loss")

        capital_risk = (
            self.config.capital
            * self.config.risk_per_trade_pct
            / 100.0
        )

        quantity = int(capital_risk // risk_per_share)

        max_value = (
            self.config.capital
            * self.config.max_position_pct
            / 100.0
        )

        if quantity * entry > max_value:
            quantity = int(max_value // entry)

        position_value = quantity * entry

        reward = abs(target - entry)

        risk_reward = (
            reward / risk_per_share
            if risk_per_share > 0
            else 0.0
        )

        return PositionResult(
            quantity=quantity,
            capital_at_risk=quantity * risk_per_share,
            position_value=position_value,
            stop_loss=stop_loss,
            target=target,
            risk_reward=round(risk_reward, 2),
        )
