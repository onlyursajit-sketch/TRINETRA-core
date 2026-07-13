from __future__ import annotations

from src.intelligence.position_sizer import PositionResult
from src.intelligence.risk_config import RiskConfig


class RiskValidator:
    """Validates whether a trade satisfies risk rules."""

    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def validate(
        self,
        result: PositionResult,
    ) -> bool:
        return (
            result.quantity > 0
            and result.risk_reward
            >= self.config.min_risk_reward
        )
