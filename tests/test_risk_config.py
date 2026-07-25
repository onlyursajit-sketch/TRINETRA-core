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


@pytest.mark.parametrize(
    "risk_per_trade_pct",
    [0.0, -1.0, 101.0],
)
def test_invalid_risk_per_trade_percentage_is_rejected(
    risk_per_trade_pct: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="Risk per trade percentage must be between 0 and 100",
    ):
        RiskConfig(
            capital=100000,
            risk_per_trade_pct=risk_per_trade_pct,
            max_position_pct=20.0,
            min_risk_reward=2.0,
        )


@pytest.mark.parametrize(
    "max_position_pct",
    [0.0, -1.0, 101.0],
)
def test_invalid_max_position_percentage_is_rejected(
    max_position_pct: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="Maximum position percentage must be between 0 and 100",
    ):
        RiskConfig(
            capital=100000,
            risk_per_trade_pct=1.0,
            max_position_pct=max_position_pct,
            min_risk_reward=2.0,
        )


@pytest.mark.parametrize(
    "min_risk_reward",
    [0.0, -1.0],
)
def test_non_positive_minimum_risk_reward_is_rejected(
    min_risk_reward: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="Minimum risk-reward must be greater than zero",
    ):
        RiskConfig(
            capital=100000,
            risk_per_trade_pct=1.0,
            max_position_pct=20.0,
            min_risk_reward=min_risk_reward,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("capital", float("nan")),
        ("risk_per_trade_pct", float("inf")),
        ("max_position_pct", float("-inf")),
        ("min_risk_reward", float("nan")),
    ],
)
def test_non_finite_risk_config_values_are_rejected(
    field: str,
    value: float,
) -> None:
    values = {
        "capital": 100000.0,
        "risk_per_trade_pct": 1.0,
        "max_position_pct": 20.0,
        "min_risk_reward": 2.0,
    }
    values[field] = value

    with pytest.raises(
        ValueError,
        match="Risk configuration values must be finite numbers",
    ):
        RiskConfig(**values)
