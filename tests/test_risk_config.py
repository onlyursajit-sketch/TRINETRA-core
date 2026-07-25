from __future__ import annotations

import pytest

from src.intelligence.risk_config import RiskConfig


def test_non_positive_capital_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Capital must be greater than zero",
    ):
        RiskConfig(
            capital=0,
            risk_per_trade_pct=1.0,
            max_position_pct=20.0,
            min_risk_reward=2.0,
        )
