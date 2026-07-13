from __future__ import annotations

import unittest

from src.intelligence.position_sizer import PositionResult
from src.intelligence.risk_config import RiskConfig
from src.intelligence.risk_validator import RiskValidator


class TestRiskValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = RiskValidator(
            RiskConfig(
                capital=100000,
                min_risk_reward=2.0,
            )
        )

    def test_valid_trade(self) -> None:
        result = PositionResult(
            quantity=100,
            capital_at_risk=1000.0,
            position_value=10000.0,
            stop_loss=95.0,
            target=110.0,
            risk_reward=2.5,
        )

        self.assertTrue(
            self.validator.validate(result)
        )

    def test_invalid_risk_reward(self) -> None:
        result = PositionResult(
            quantity=100,
            capital_at_risk=1000.0,
            position_value=10000.0,
            stop_loss=95.0,
            target=105.0,
            risk_reward=1.0,
        )

        self.assertFalse(
            self.validator.validate(result)
        )

    def test_zero_quantity(self) -> None:
        result = PositionResult(
            quantity=0,
            capital_at_risk=0.0,
            position_value=0.0,
            stop_loss=95.0,
            target=110.0,
            risk_reward=3.0,
        )

        self.assertFalse(
            self.validator.validate(result)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
