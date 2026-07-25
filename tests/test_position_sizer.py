from __future__ import annotations

import unittest

import pytest

from src.intelligence.position_sizer import PositionSizer
from src.intelligence.risk_config import RiskConfig


class TestPositionSizer(unittest.TestCase):
    def setUp(self) -> None:
        self.sizer = PositionSizer(
            RiskConfig(
                capital=100000,
                risk_per_trade_pct=1.0,
                max_position_pct=20.0,
                min_risk_reward=2.0,
            )
        )

    def test_position_size(self) -> None:
        result = self.sizer.calculate(
            entry=100.0,
            stop_loss=95.0,
            target=110.0,
        )

        self.assertEqual(result.quantity, 200)
        self.assertEqual(result.capital_at_risk, 1000.0)
        self.assertEqual(result.position_value, 20000.0)
        self.assertEqual(result.risk_reward, 2.0)

    def test_invalid_stop_loss(self) -> None:
        with self.assertRaises(ValueError):
            self.sizer.calculate(
                entry=100.0,
                stop_loss=100.0,
                target=120.0,
            )

    def test_position_cap(self) -> None:
        result = self.sizer.calculate(
            entry=500.0,
            stop_loss=495.0,
            target=520.0,
        )

        self.assertLessEqual(result.position_value, 20000.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)


def test_non_positive_entry_is_rejected() -> None:
    sizer = PositionSizer(
        RiskConfig(
            capital=100000,
            risk_per_trade_pct=1.0,
            max_position_pct=20.0,
            min_risk_reward=2.0,
        )
    )

    with pytest.raises(
        ValueError,
        match="Entry price must be greater than zero",
    ):
        sizer.calculate(
            entry=0.0,
            stop_loss=95.0,
            target=110.0,
        )


def test_non_positive_stop_loss_is_rejected() -> None:
    sizer = PositionSizer(
        RiskConfig(
            capital=100000,
            risk_per_trade_pct=1.0,
            max_position_pct=20.0,
            min_risk_reward=2.0,
        )
    )

    with pytest.raises(
        ValueError,
        match="Stop-loss price must be greater than zero",
    ):
        sizer.calculate(
            entry=100.0,
            stop_loss=0.0,
            target=110.0,
        )
