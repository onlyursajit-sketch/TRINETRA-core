from __future__ import annotations

import unittest

from src.market.market_engine import MarketEngine


class FakeOptionsPipeline:
    def run(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "data_status": "LIVE",
            "analytics_allowed": True,
        }


class FakeSnapshotEngine:
    def build(
        self,
        options_result: dict,
        vix_result: dict,
        flows_result: dict,
    ) -> dict:
        return {
            "symbol": "NIFTY",
            "market_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "confidence": "HIGH",
            "institutional_score": 40,
            "warnings": [],
            "pcr": {
                "overall_pcr": 1.08,
            },
            "india_vix": {
                "risk_regime": "LOW",
                "direction": "DOWN",
            },
            "fii_dii": {
                "market_bias": "DOMESTICALLY_SUPPORTED",
            },
        }


class FakeMarketReportGenerator:
    def render(self, snapshot: dict) -> str:
        return "MARKET REPORT"


class FakeGlobalCommandCenter:
    def build(self, payloads: dict) -> dict:
        return {
            "health": "LIVE",
            "global_bias": "BULLISH",
            "source_confidence": 90,
            "warnings": [],
            "summary": {},
            "markets": [],
        }


class FakeGlobalReportGenerator:
    def render(self, command_center: dict) -> str:
        return "GLOBAL REPORT"


class TestMarketAIIntegration(unittest.TestCase):
    def test_ai_decision_is_added_to_market_result(self) -> None:
        engine = MarketEngine(
            options_pipeline=FakeOptionsPipeline(),
            snapshot_engine=FakeSnapshotEngine(),
            report_generator=FakeMarketReportGenerator(),
            global_command_center=FakeGlobalCommandCenter(),
            global_report_generator=FakeGlobalReportGenerator(),
        )

        result = engine.build(
            "NIFTY",
            global_payloads={},
        )

        self.assertIn(
            "ai_decision",
            result,
        )

        self.assertEqual(
            result["ai_decision"]["decision"],
            "BUY_BIAS",
        )

        self.assertEqual(
            result["ai_decision"]["action"],
            "WAIT_FOR_LONG_CONFIRMATION",
        )

        self.assertIn(
            "TRINETRA — AI DECISION HUB",
            result["report"],
        )

    def test_invalid_symbol_is_blocked(self) -> None:
        engine = MarketEngine(
            options_pipeline=FakeOptionsPipeline(),
            snapshot_engine=FakeSnapshotEngine(),
            report_generator=FakeMarketReportGenerator(),
            global_command_center=FakeGlobalCommandCenter(),
            global_report_generator=FakeGlobalReportGenerator(),
        )

        with self.assertRaises(Exception):
            engine.build("   ")


if __name__ == "__main__":
    unittest.main(verbosity=2)


def test_ai_decision_exposes_trade_quality_and_explanation() -> None:
    engine = MarketEngine(
        options_pipeline=FakeOptionsPipeline(),
        snapshot_engine=FakeSnapshotEngine(),
        report_generator=FakeMarketReportGenerator(),
        global_command_center=FakeGlobalCommandCenter(),
        global_report_generator=FakeGlobalReportGenerator(),
    )

    result = engine.build(
        "NIFTY",
        global_payloads={},
    )

    ai_decision = result["ai_decision"]

    assert "trade_quality_score" in ai_decision
    assert "explanation" in ai_decision
    assert ai_decision["explanation"]["reasons"] == ai_decision["reasons"]
    assert ai_decision["explanation"]["warnings"] == ai_decision["warnings"]


class FakeInjectedDecisionHub:
    def __init__(self) -> None:
        self.received_market_result = None

    def decide(self, market_result: dict) -> dict:
        self.received_market_result = market_result
        return {
            "decision": "WAIT",
            "action": "WAIT",
            "score": 0.0,
            "confidence_score": 50.0,
            "confidence": "MODERATE",
            "risk_score": 0.0,
            "risk": "LOW",
            "trade_quality_score": 50.0,
            "reasons": [],
            "warnings": [],
            "explanation": {
                "summary": "Injected decision hub.",
                "reasons": [],
                "warnings": [],
            },
            "why": {},
            "rule": "Decision support only.",
        }


def test_market_engine_accepts_injected_decision_hub() -> None:
    decision_hub = FakeInjectedDecisionHub()

    engine = MarketEngine(
        options_pipeline=FakeOptionsPipeline(),
        snapshot_engine=FakeSnapshotEngine(),
        report_generator=FakeMarketReportGenerator(),
        global_command_center=FakeGlobalCommandCenter(),
        global_report_generator=FakeGlobalReportGenerator(),
        decision_hub=decision_hub,
    )

    result = engine.build(
        "NIFTY",
        global_payloads={},
    )

    assert result["ai_decision"]["decision"] == "WAIT"
    assert decision_hub.received_market_result is not None
    assert "global" in decision_hub.received_market_result
    assert "snapshot" in decision_hub.received_market_result


def test_market_engine_exposes_execution_trace() -> None:
    engine = MarketEngine(
        options_pipeline=FakeOptionsPipeline(),
        snapshot_engine=FakeSnapshotEngine(),
        report_generator=FakeMarketReportGenerator(),
        global_command_center=FakeGlobalCommandCenter(),
        global_report_generator=FakeGlobalReportGenerator(),
    )

    result = engine.build(
        "NIFTY",
        global_payloads={},
    )

    assert result["execution_trace"] == [
        "OPTIONS_ANALYTICS",
        "GLOBAL_COMMAND_CENTER",
        "INDIA_VIX",
        "FII_DII",
        "MARKET_SNAPSHOT",
        "GLOBAL_REPORT",
        "MARKET_REPORT",
        "AI_DECISION",
    ]


class FailingDecisionHub:
    def decide(self, market_result: dict) -> dict:
        raise RuntimeError("decision hub unavailable")


def test_market_engine_survives_decision_hub_failure() -> None:
    engine = MarketEngine(
        options_pipeline=FakeOptionsPipeline(),
        snapshot_engine=FakeSnapshotEngine(),
        report_generator=FakeMarketReportGenerator(),
        global_command_center=FakeGlobalCommandCenter(),
        global_report_generator=FakeGlobalReportGenerator(),
        decision_hub=FailingDecisionHub(),
    )

    result = engine.build(
        "NIFTY",
        global_payloads={},
    )

    assert result["ai_decision"]["decision"] == "NO_TRADE"
    assert result["ai_decision"]["action"] == "WAIT"
    assert result["ai_decision"]["warnings"] == [
        "Decision engine unavailable."
    ]
    assert result["execution_status"] == "PARTIAL"
    assert result["failed_stages"] == ["AI_DECISION"]
