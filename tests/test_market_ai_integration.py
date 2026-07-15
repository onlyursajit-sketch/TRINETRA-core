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
