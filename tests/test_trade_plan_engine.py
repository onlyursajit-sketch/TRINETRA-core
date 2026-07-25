from __future__ import annotations

import unittest

from src.intelligence.risk_config import RiskConfig
from src.intelligence.trade_plan_engine import TradePlanEngine


class TestTradePlanEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = TradePlanEngine(
            RiskConfig(
                capital=100000,
                risk_per_trade_pct=1.0,
                max_position_pct=20.0,
                min_risk_reward=2.0,
            )
        )

    def test_valid_trade_plan(self) -> None:
        plan = self.engine.create(
            entry=100.0,
            stop_loss=95.0,
            target=110.0,
        )

        self.assertTrue(plan.approved)
        self.assertEqual(plan.quantity, 200)
        self.assertEqual(plan.risk_reward, 2.0)

    def test_invalid_trade_plan(self) -> None:
        plan = self.engine.create(
            entry=100.0,
            stop_loss=95.0,
            target=103.0,
        )

        self.assertFalse(plan.approved)
        self.assertEqual(
            plan.reason,
            "Risk-reward 0.60 is below required minimum 2.00.",
        )

    def test_position_value_limit(self) -> None:
        plan = self.engine.create(
            entry=500.0,
            stop_loss=495.0,
            target=520.0,
        )

        self.assertLessEqual(
            plan.position_value,
            20000.0,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)


def test_trade_plan_explains_low_risk_reward_rejection() -> None:
    engine = TradePlanEngine(
        RiskConfig(
            capital=100000,
            risk_per_trade_pct=1.0,
            max_position_pct=20.0,
            min_risk_reward=2.0,
        )
    )

    plan = engine.create(
        entry=100.0,
        stop_loss=95.0,
        target=103.0,
    )

    assert plan.approved is False
    assert plan.reason == (
        "Risk-reward 0.60 is below required minimum 2.00."
    )
