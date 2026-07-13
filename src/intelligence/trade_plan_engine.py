from __future__ import annotations

from dataclasses import dataclass

from src.intelligence.position_sizer import PositionSizer
from src.intelligence.risk_config import RiskConfig
from src.intelligence.risk_validator import RiskValidator


@dataclass(frozen=True)
class TradePlan:
    approved: bool
    quantity: int
    entry: float
    stop_loss: float
    target: float
    capital_at_risk: float
    position_value: float
    risk_reward: float
    reason: str


class TradePlanEngine:
    """Creates a risk-managed trade execution plan."""

    def __init__(self, config: RiskConfig) -> None:
        self.sizer = PositionSizer(config)
        self.validator = RiskValidator(config)

    def create(
        self,
        entry: float,
        stop_loss: float,
        target: float,
    ) -> TradePlan:
        result = self.sizer.calculate(
            entry=entry,
            stop_loss=stop_loss,
            target=target,
        )

        approved = self.validator.validate(result)

        reason = (
            "Trade satisfies risk rules."
            if approved
            else "Trade rejected by risk rules."
        )

        return TradePlan(
            approved=approved,
            quantity=result.quantity,
            entry=entry,
            stop_loss=result.stop_loss,
            target=result.target,
            capital_at_risk=result.capital_at_risk,
            position_value=result.position_value,
            risk_reward=result.risk_reward,
            reason=reason,
        )
