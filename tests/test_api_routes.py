from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.app import app
import src.api.routes.market as market_route
import src.api.routes.signal as signal_route


client = TestClient(app)


@dataclass
class FakeContext:
    symbol: str
    confidence: float = 75.0
    market_regime: str = "NEUTRAL"


@dataclass
class FakeSignal:
    symbol: str
    action: str = "HOLD"
    confidence: float = 75.0
    risk_score: float = 25.0


class FakeBuilder:
    def build(self, symbol: str = "NIFTY") -> FakeContext:
        return FakeContext(symbol=symbol)


class FakeSignalEngine:
    def generate(self, context: FakeContext) -> FakeSignal:
        return FakeSignal(symbol=context.symbol)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "TRINETRA",
        "status": "running",
        "version": "1.0.0",
    }


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "TRINETRA"


def test_market_context_endpoint() -> None:
    with patch.object(market_route, "builder", FakeBuilder()):
        response = client.get(
            "/market/context",
            params={"symbol": "BANKNIFTY"},
        )

    assert response.status_code == 200
    assert response.json()["symbol"] == "BANKNIFTY"
    assert response.json()["confidence"] == 75.0


def test_signal_endpoint() -> None:
    with (
        patch.object(signal_route, "builder", FakeBuilder()),
        patch.object(signal_route, "engine", FakeSignalEngine()),
    ):
        response = client.get(
            "/signal",
            params={"symbol": "NIFTY"},
        )

    assert response.status_code == 200
    assert response.json()["symbol"] == "NIFTY"
    assert response.json()["action"] == "HOLD"


def test_trade_plan_endpoint() -> None:
    response = client.post(
        "/trade/plan",
        json={
            "capital": 100000,
            "entry": 100,
            "stop_loss": 95,
            "target": 110,
            "risk_per_trade_pct": 1.0,
            "max_position_pct": 20.0,
            "min_risk_reward": 2.0,
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_trade_plan_validation() -> None:
    response = client.post(
        "/trade/plan",
        json={
            "capital": -1000,
            "entry": 0,
            "stop_loss": 95,
            "target": 110,
        },
    )

    assert response.status_code == 422
