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


class FakeProviderManager:
    def provider_health_report(self) -> dict:
        return {
            "NSE": {
                "success_count": 4,
                "failure_count": 1,
                "success_rate": 80.0,
                "total_calls": 5,
                "average_latency_ms": 120.5,
                "last_latency_ms": 110.0,
                "available": True,
                "circuit_open_until": None,
            },
            "DHAN": {
                "success_count": 0,
                "failure_count": 2,
                "success_rate": 0.0,
                "total_calls": 2,
                "average_latency_ms": 250.0,
                "last_latency_ms": 240.0,
                "available": False,
                "circuit_open_until": None,
            },
        }

    def manager_health_summary(self) -> dict:
        return {
            "status": "DEGRADED",
            "providers_total": 2,
            "providers_available": 1,
            "providers_unavailable": 1,
            "total_attempts": 7,
            "total_successes": 4,
            "overall_success_rate": 57.14,
        }


def test_provider_health_endpoint() -> None:
    with patch.object(
        market_route,
        "provider_manager",
        FakeProviderManager(),
        create=True,
    ):
        response = client.get("/market/providers/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["summary"]["status"] == "DEGRADED"
    assert payload["summary"]["providers_available"] == 1
    assert payload["providers"]["NSE"]["available"] is True
    assert payload["providers"]["DHAN"]["failure_count"] == 2


def test_market_decision_endpoint() -> None:
    fake_decision = {
        "engine": "TRINETRA_AI_DECISION_HUB",
        "decision": "BUY_BIAS",
        "action": "WAIT_FOR_LONG_CONFIRMATION",
        "score": 75.0,
        "confidence_score": 80.0,
        "confidence": "HIGH",
        "risk_score": 20.0,
        "trade_quality_score": 82.0,
        "risk": "LOW",
        "reasons": ["Bullish alignment"],
        "warnings": [],
        "explanation": {
            "summary": "BUY_BIAS with HIGH confidence and LOW risk.",
            "reasons": ["Bullish alignment"],
            "warnings": [],
        },
    }

    with patch.object(
        market_route,
        "build_market_decision",
        return_value=fake_decision,
        create=True,
    ):
        response = client.get(
            "/market/decision",
            params={"symbol": "NIFTY"},
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["decision"] == "BUY_BIAS"
    assert payload["confidence_score"] == 80.0
    assert payload["risk_score"] == 20.0
    assert payload["trade_quality_score"] == 82.0
    assert payload["explanation"]["summary"]


def test_market_decision_endpoint() -> None:
    fake_decision = {
        "engine": "TRINETRA_AI_DECISION_HUB",
        "decision": "BUY_BIAS",
        "action": "WAIT_FOR_LONG_CONFIRMATION",
        "score": 75.0,
        "confidence_score": 80.0,
        "confidence": "HIGH",
        "risk_score": 20.0,
        "trade_quality_score": 82.0,
        "risk": "LOW",
        "reasons": ["Bullish alignment"],
        "warnings": [],
        "explanation": {
            "summary": "BUY_BIAS with HIGH confidence and LOW risk.",
            "reasons": ["Bullish alignment"],
            "warnings": [],
        },
    }

    with patch.object(
        market_route,
        "build_market_decision",
        return_value=fake_decision,
        create=True,
    ):
        response = client.get(
            "/market/decision",
            params={"symbol": "NIFTY"},
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["decision"] == "BUY_BIAS"
    assert payload["confidence_score"] == 80.0
    assert payload["risk_score"] == 20.0
    assert payload["trade_quality_score"] == 82.0
    assert payload["explanation"]["summary"]


def test_market_decision_endpoint_contract() -> None:
    fake_decision = {
        "engine": "TRINETRA_AI_DECISION_HUB",
        "decision": "WAIT",
        "action": "WAIT",
        "score": 50.0,
        "confidence_score": 65.0,
        "confidence": "MEDIUM",
        "risk_score": 35.0,
        "trade_quality_score": 65.0,
        "risk": "MEDIUM",
        "reasons": ["Mixed market signals"],
        "warnings": [],
        "explanation": {
            "summary": "WAIT with MEDIUM confidence and MEDIUM risk.",
            "reasons": ["Mixed market signals"],
            "warnings": [],
        },
    }

    with patch.object(
        market_route,
        "build_market_decision",
        return_value=fake_decision,
    ):
        response = client.get("/market/decision?symbol=NIFTY")

    assert response.status_code == 200

    payload = response.json()

    required_fields = {
        "decision",
        "action",
        "confidence_score",
        "risk_score",
        "trade_quality_score",
        "explanation",
    }

    assert required_fields.issubset(payload)
    assert isinstance(payload["explanation"], dict)


def test_market_decision_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TRINETRA_API_KEY", "secret-key")

    response = client.get(
        "/market/decision",
        params={"symbol": "NIFTY"},
    )

    assert response.status_code == 401


def test_market_decision_accepts_valid_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TRINETRA_API_KEY", "secret-key")

    fake_decision = {
        "decision": "WAIT",
        "action": "WAIT",
        "confidence_score": 60.0,
        "risk_score": 40.0,
        "trade_quality_score": 60.0,
        "explanation": {
            "summary": "WAIT",
            "reasons": [],
            "warnings": [],
        },
    }

    with patch.object(
        market_route,
        "build_market_decision",
        return_value=fake_decision,
    ):
        response = client.get(
            "/market/decision",
            params={"symbol": "NIFTY"},
            headers={"X-API-Key": "secret-key"},
        )

    assert response.status_code == 200
    assert response.json()["decision"] == "WAIT"


def test_signal_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TRINETRA_API_KEY", "secret-key")

    response = client.get(
        "/signal",
        params={"symbol": "NIFTY"},
    )

    assert response.status_code == 401


def test_trade_plan_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TRINETRA_API_KEY", "secret-key")

    response = client.post(
        "/trade/plan",
        json={
            "capital": 100000,
            "entry": 100,
            "stop_loss": 95,
            "target": 110,
        },
    )

    assert response.status_code == 401


def test_trade_plan_accepts_valid_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TRINETRA_API_KEY", "secret-key")

    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "secret-key"},
        json={
            "capital": 100000,
            "entry": 100,
            "stop_loss": 95,
            "target": 110,
        },
    )

    assert response.status_code == 200


def test_openapi_exposes_api_key_security_scheme() -> None:
    schema = client.get("/openapi.json").json()

    security_schemes = (
        schema
        .get("components", {})
        .get("securitySchemes", {})
    )

    assert security_schemes

    api_key_schemes = [
        value
        for value in security_schemes.values()
        if value.get("type") == "apiKey"
        and value.get("name") == "X-API-Key"
        and value.get("in") == "header"
    ]

    assert api_key_schemes


def test_protected_routes_are_marked_secure_in_openapi() -> None:
    schema = client.get("/openapi.json").json()

    protected_operations = [
        schema["paths"]["/market/decision"]["get"],
        schema["paths"]["/signal/"]["get"]
        if "/signal/" in schema["paths"]
        else schema["paths"]["/signal"]["get"],
        schema["paths"]["/trade/plan"]["post"],
    ]

    for operation in protected_operations:
        assert operation.get("security")


def test_versioned_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["service"] == "TRINETRA"


def test_versioned_market_context_endpoint() -> None:
    with patch.object(market_route, "builder", FakeBuilder()):
        response = client.get(
            "/api/v1/market/context",
            params={"symbol": "BANKNIFTY"},
        )

    assert response.status_code == 200
    assert response.json()["symbol"] == "BANKNIFTY"


def test_versioned_market_decision_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TRINETRA_API_KEY", "secret-key")

    response = client.get(
        "/api/v1/market/decision",
        params={"symbol": "NIFTY"},
    )

    assert response.status_code == 401


def test_versioned_signal_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TRINETRA_API_KEY", "secret-key")

    response = client.get(
        "/api/v1/signal",
        params={"symbol": "NIFTY"},
    )

    assert response.status_code == 401


def test_versioned_trade_plan_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TRINETRA_API_KEY", "secret-key")

    response = client.post(
        "/api/v1/trade/plan",
        json={
            "capital": 100000,
            "entry": 100,
            "stop_loss": 95,
            "target": 110,
        },
    )

    assert response.status_code == 401


def test_root_and_health_versions_match() -> None:
    root_response = client.get("/")
    health_response = client.get("/health")

    assert root_response.status_code == 200
    assert health_response.status_code == 200
    assert root_response.json()["version"] == health_response.json()["version"]


def test_cors_allows_vite_frontend_origin() -> None:
    response = client.options(
        "/api/v1/market/context",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )


def test_market_option_chain_endpoint(monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from src.api.app import app
    from src.api.routes import market

    monkeypatch.setattr(
        market.options_pipeline,
        "run",
        lambda symbol: {
            "symbol": symbol,
            "data_status": "LIVE",
            "option_chain": {
                "symbol": symbol,
                "records": [
                    {
                        "strikePrice": 25000,
                        "CE": {"openInterest": 100},
                        "PE": {"openInterest": 120},
                    }
                ],
                "source": "TEST",
                "data_status": "LIVE",
                "manager_status": "SUCCESS",
                "provider_used": "TEST",
                "fallback_used": False,
                "provider_errors": [],
            },
            "oi": None,
            "pcr": None,
            "max_pain": None,
            "volume_analysis": None,
            "analytics_allowed": False,
            "errors": [],
        },
    )

    response = TestClient(app).get(
        "/api/v1/market/option-chain",
        params={"symbol": "nifty"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["symbol"] == "NIFTY"
    assert payload["data_status"] == "LIVE"
    assert payload["provider_used"] == "TEST"
    assert len(payload["records"]) == 1

def test_market_option_chain_endpoint_includes_analytics(monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from src.api.app import app
    from src.api.routes import market

    monkeypatch.setattr(
        market,
        "options_pipeline",
        type(
            "FakePipeline",
            (),
            {
                "run": lambda self, symbol: {
                    "symbol": symbol,
                    "data_status": "LIVE",
                    "option_chain": {
                        "symbol": symbol,
                        "records": [{"strike_price": 25000}],
                        "source": "TEST",
                        "data_status": "LIVE",
                        "provider_used": "TEST",
                    },
                    "pcr": {
                        "overall_pcr": 1.25,
                        "market_bias": "BULLISH",
                    },
                    "max_pain": {
                        "max_pain_strike": 25000,
                    },
                    "oi": {
                        "market_bias": "BULLISH",
                    },
                    "volume_analysis": {
                        "market_bias": "BULLISH",
                    },
                }
            },
        )(),
    )

    response = TestClient(app).get(
        "/api/v1/market/option-chain",
        params={"symbol": "nifty"},
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["symbol"] == "NIFTY"
    assert payload["records"] == [{"strike_price": 25000}]
    assert payload["pcr"] == 1.25
    assert payload["max_pain"] == 25000
    assert payload["oi_bias"] == "BULLISH"
    assert payload["volume_bias"] == "BULLISH"

def test_market_context_uses_option_analytics_snapshot(monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from src.api.app import app
    from src.api.routes import market

    captured = {}

    class FakeBuilder:
        def build(self, **kwargs):
            from src.intelligence.context_builder import MarketContext

            captured.update(kwargs)
            return MarketContext(
                symbol=kwargs.get("symbol", "NIFTY"),
                confidence=75.0,
            )

    class FakePipeline:
        def run(self, symbol):
            return {
                "symbol": symbol,
                "data_status": "STALE",
                "option_chain": {
                    "symbol": symbol,
                    "records": [],
                    "data_status": "STALE",
                },
                "pcr": {
                    "overall_pcr": 0.98,
                    "market_bias": "NEUTRAL_BEARISH",
                },
                "max_pain": {
                    "max_pain_strike": 25000.0,
                },
                "oi": {
                    "market_bias": "BULLISH",
                },
                "volume_analysis": {
                    "market_bias": "BULLISH",
                },
                "analytics_allowed": True,
                "errors": [],
            }

    monkeypatch.setattr(market, "builder", FakeBuilder())
    monkeypatch.setattr(market, "options_pipeline", FakePipeline())

    response = TestClient(app).get(
        "/api/v1/market/context",
        params={"symbol": "NIFTY"},
    )

    assert response.status_code == 200
    assert captured["options_result"]["pcr"]["overall_pcr"] == 0.9804
    assert captured["options_result"]["max_pain"]["max_pain_strike"] == 25000.0

def test_market_decision_receives_option_analytics_snapshot(monkeypatch) -> None:
    from fastapi.testclient import TestClient
    from src.api.app import app
    from src.api.routes import market

    captured = {}

    from dataclasses import dataclass

    @dataclass
    class FakeContext:
        symbol: str = "NIFTY"
        confidence: float = 75.0

    class FakeBuilder:
        def build(self, **kwargs):
            return FakeContext()

    class FakePipeline:
        def run(self, symbol):
            return {
                "symbol": symbol,
                "data_status": "LIVE",
                "option_chain": {
                    "symbol": symbol,
                    "records": [],
                    "data_status": "LIVE",
                },
                "pcr": {
                    "overall_pcr": 1.12,
                    "market_bias": "BULLISH",
                },
                "max_pain": {
                    "max_pain_strike": 25000.0,
                },
                "oi": {
                    "market_bias": "BULLISH",
                },
                "volume_analysis": {
                    "market_bias": "BULLISH",
                },
                "analytics_allowed": True,
                "errors": [],
            }

    class FakeDecisionHub:
        def decide(self, payload):
            captured.update(payload)
            return {
                "decision": "WAIT",
                "confidence_score": 50,
                "risk_score": 10,
                "trade_quality_score": 40,
                "market_status": "LIVE",
                "explanation": {
                    "summary": "test",
                    "reasons": [],
                },
            }

    monkeypatch.setattr(market, "builder", FakeBuilder())
    monkeypatch.setattr(market, "options_pipeline", FakePipeline())
    monkeypatch.setattr(market, "AIDecisionHub", FakeDecisionHub)

    response = TestClient(app).get("/api/v1/market/decision?symbol=NIFTY")

    assert response.status_code == 200
    assert captured["snapshot"]["pcr"]["overall_pcr"] == 1.12
    assert captured["snapshot"]["max_pain"]["max_pain_strike"] == 25000.0
    assert captured["snapshot"]["oi"]["market_bias"] == "BULLISH"
    assert captured["snapshot"]["volume_analysis"]["market_bias"] == "BULLISH"



def test_trade_plan_api_exposes_direction() -> None:
    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "test-key"},
        json={
            "capital": 100000,
            "entry": 100.0,
            "stop_loss": 95.0,
            "target": 110.0,
            "risk_per_trade_pct": 1.0,
            "max_position_pct": 20.0,
            "min_risk_reward": 2.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["direction"] == "LONG"


def test_trade_plan_api_exposes_short_direction() -> None:
    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "test-key"},
        json={
            "capital": 100000,
            "entry": 100.0,
            "stop_loss": 105.0,
            "target": 90.0,
            "risk_per_trade_pct": 1.0,
            "max_position_pct": 20.0,
            "min_risk_reward": 2.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["direction"] == "SHORT"


def test_trade_plan_api_rejects_invalid_trade_prices() -> None:
    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "test-key"},
        json={
            "capital": 100000,
            "entry": 100.0,
            "stop_loss": 95.0,
            "target": 90.0,
            "risk_per_trade_pct": 1.0,
            "max_position_pct": 20.0,
            "min_risk_reward": 2.0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Stop-loss and target must be on opposite sides of entry price"
    )


def test_trade_plan_api_rejects_invalid_risk_config() -> None:
    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "test-key"},
        json={
            "capital": 100000,
            "entry": 100.0,
            "stop_loss": 95.0,
            "target": 110.0,
            "risk_per_trade_pct": 101.0,
            "max_position_pct": 20.0,
            "min_risk_reward": 2.0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Risk per trade percentage must be between 0 and 100"
    )


def test_trade_plan_api_rejects_invalid_max_position_percentage() -> None:
    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "test-key"},
        json={
            "capital": 100000,
            "entry": 100.0,
            "stop_loss": 95.0,
            "target": 110.0,
            "risk_per_trade_pct": 1.0,
            "max_position_pct": 101.0,
            "min_risk_reward": 2.0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Maximum position percentage must be between 0 and 100"
    )


def test_trade_plan_api_rejects_invalid_minimum_risk_reward() -> None:
    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "test-key"},
        json={
            "capital": 100000,
            "entry": 100.0,
            "stop_loss": 95.0,
            "target": 110.0,
            "risk_per_trade_pct": 1.0,
            "max_position_pct": 20.0,
            "min_risk_reward": 0.0,
        },
    )

    assert response.status_code == 422

    detail = response.json()["detail"]
    assert detail[0]["loc"][-1] == "min_risk_reward"


def test_trade_plan_api_rejects_non_positive_capital() -> None:
    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "test-key"},
        json={
            "capital": 0,
            "entry": 100.0,
            "stop_loss": 95.0,
            "target": 110.0,
            "risk_per_trade_pct": 1.0,
            "max_position_pct": 20.0,
            "min_risk_reward": 2.0,
        },
    )

    assert response.status_code == 422

    detail = response.json()["detail"]
    assert detail[0]["loc"][-1] == "capital"


def test_trade_plan_api_rejects_non_positive_entry() -> None:
    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "test-key"},
        json={
            "capital": 100000,
            "entry": 0.0,
            "stop_loss": 95.0,
            "target": 110.0,
            "risk_per_trade_pct": 1.0,
            "max_position_pct": 20.0,
            "min_risk_reward": 2.0,
        },
    )

    assert response.status_code == 422

    detail = response.json()["detail"]
    assert detail[0]["loc"][-1] == "entry"


def test_trade_plan_api_rejects_non_positive_stop_loss() -> None:
    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "test-key"},
        json={
            "capital": 100000,
            "entry": 100.0,
            "stop_loss": 0.0,
            "target": 110.0,
            "risk_per_trade_pct": 1.0,
            "max_position_pct": 20.0,
            "min_risk_reward": 2.0,
        },
    )

    assert response.status_code == 422

    detail = response.json()["detail"]
    assert detail[0]["loc"][-1] == "stop_loss"


def test_trade_plan_api_rejects_non_positive_target() -> None:
    response = client.post(
        "/trade/plan",
        headers={"X-API-Key": "test-key"},
        json={
            "capital": 100000,
            "entry": 100.0,
            "stop_loss": 95.0,
            "target": 0.0,
            "risk_per_trade_pct": 1.0,
            "max_position_pct": 20.0,
            "min_risk_reward": 2.0,
        },
    )

    assert response.status_code == 422

    detail = response.json()["detail"]
    assert detail[0]["loc"][-1] == "target"
