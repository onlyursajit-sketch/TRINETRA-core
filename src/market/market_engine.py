from __future__ import annotations

from typing import Any

from src.decision.ai_decision import AIDecisionHub

from src.global_command.global_command_center import (
    GlobalCommandCenter,
)
from src.pipelines.options_analytics_pipeline import (
    OptionsAnalyticsPipeline,
)
from src.reports.global_market_report import (
    GlobalMarketReportGenerator,
)
from src.reports.market_report import (
    MarketReportGenerator,
)
from src.snapshot.market_snapshot import (
    MarketSnapshotEngine,
)


class MarketEngineError(Exception):
    """Raised when TRINETRA MARKET orchestration fails."""


class MarketEngine:
    """
    TRINETRA end-to-end MARKET orchestration engine.

    Current flow:
    Global Command Center
        +
    Options Analytics
        +
    India VIX
        +
    FII/DII
        ↓
    Unified Snapshot
        ↓
    Final MARKET Report
    """

    def __init__(
        self,
        options_pipeline: OptionsAnalyticsPipeline | None = None,
        snapshot_engine: MarketSnapshotEngine | None = None,
        report_generator: MarketReportGenerator | None = None,
        global_command_center: GlobalCommandCenter | None = None,
        global_report_generator: GlobalMarketReportGenerator | None = None,
        decision_hub: AIDecisionHub | None = None,
    ) -> None:
        self.options_pipeline = (
            options_pipeline
            or OptionsAnalyticsPipeline()
        )

        self.snapshot_engine = (
            snapshot_engine
            or MarketSnapshotEngine()
        )

        self.report_generator = (
            report_generator
            or MarketReportGenerator()
        )

        self.global_command_center = (
            global_command_center
            or GlobalCommandCenter()
        )

        self.global_report_generator = (
            global_report_generator
            or GlobalMarketReportGenerator()
        )

        self.decision_hub = (
            decision_hub
            or AIDecisionHub()
        )

    @staticmethod
    def _missing_vix_payload() -> dict[str, Any]:
        return {
            "symbol": "INDIA_VIX",
            "source": None,
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "previous_close": None,
            "open": None,
            "high": None,
            "low": None,
            "current": None,
            "difference": None,
            "percentage_change": None,
            "risk_regime": "UNAVAILABLE",
            "direction": "UNAVAILABLE",
            "impact": (
                "India VIX live data source is not connected."
            ),
        }

    @staticmethod
    def _missing_fii_dii_payload() -> dict[str, Any]:
        return {
            "source": None,
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "trade_date": None,
            "participant_table": [],
            "fii": {
                "cash_net": None,
            },
            "dii": {
                "cash_net": None,
            },
            "combined_cash_net": None,
            "market_bias": "UNAVAILABLE",
            "flow_structure": "UNAVAILABLE",
            "interpretation": (
                "FII/DII live data source is not connected."
            ),
        }

    def build(
        self,
        symbol: str = "NIFTY",
        global_payloads: dict[
            str,
            dict[str, Any]
        ] | None = None,
        india_vix_payload: dict[str, Any] | None = None,
        fii_dii_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        clean_symbol = symbol.strip().upper()

        if not clean_symbol:
            raise MarketEngineError(
                "Market symbol cannot be empty."
            )

        execution_trace: list[str] = []

        options_result = self.options_pipeline.run(
            clean_symbol
        )
        execution_trace.append("OPTIONS_ANALYTICS")

        global_result = (
            self.global_command_center.build(
                global_payloads
                if isinstance(global_payloads, dict)
                else {}
            )
        )
        execution_trace.append("GLOBAL_COMMAND_CENTER")

        vix_result = (
            india_vix_payload
            if isinstance(india_vix_payload, dict)
            else self._missing_vix_payload()
        )
        execution_trace.append("INDIA_VIX")

        flows_result = (
            fii_dii_payload
            if isinstance(fii_dii_payload, dict)
            else self._missing_fii_dii_payload()
        )
        execution_trace.append("FII_DII")

        snapshot = self.snapshot_engine.build(
            options_result,
            vix_result,
            flows_result,
        )
        execution_trace.append("MARKET_SNAPSHOT")

        global_report = (
            self.global_report_generator.render(
                global_result
            )
        )
        execution_trace.append("GLOBAL_REPORT")

        market_report = self.report_generator.render(
            snapshot
        )
        execution_trace.append("MARKET_REPORT")

        failed_stages: list[str] = []

        try:
            decision = self.decision_hub.decide(
                {
                    "global": global_result,
                    "snapshot": snapshot,
                }
            )
            execution_trace.append("AI_DECISION")
        except Exception:
            decision = {
                "decision": "NO_TRADE",
                "action": "WAIT",
                "score": 0.0,
                "confidence_score": 0.0,
                "confidence": "LOW",
                "risk_score": 100.0,
                "risk": "HIGH",
                "trade_quality_score": 0.0,
                "reasons": [],
                "warnings": [
                    "Decision engine unavailable."
                ],
                "explanation": {
                    "summary": (
                        "Decision engine unavailable; "
                        "no trade decision issued."
                    ),
                    "reasons": [],
                    "warnings": [
                        "Decision engine unavailable."
                    ],
                },
                "why": {},
                "rule": (
                    "Decision support only. "
                    "No standalone prediction."
                ),
            }
            failed_stages.append("AI_DECISION")

        ai_lines = [
            "=" * 68,
            "TRINETRA — AI DECISION HUB",
            "=" * 68,
            f"Decision            : {decision['decision']}",
            f"Action              : {decision['action']}",
            f"Score               : {decision['score']}",
            f"Confidence Score    : {decision['confidence_score']}",
            f"Confidence          : {decision['confidence']}",
            f"Risk Score          : {decision['risk_score']}",
            f"Risk                : {decision['risk']}",
            "",
            "Reasons:",
        ]

        reasons = decision.get("reasons", [])

        if reasons:
            for reason in reasons:
                ai_lines.append(f"- {reason}")
        else:
            ai_lines.append("- NONE")

        ai_lines.extend(
            [
                "",
                "Warnings:",
            ]
        )

        decision_warnings = decision.get(
            "warnings",
            [],
        )

        if decision_warnings:
            for warning in decision_warnings:
                ai_lines.append(f"- {warning}")
        else:
            ai_lines.append("- NONE")

        ai_lines.extend(
            [
                "",
                f"Rule                : {decision['rule']}",
            ]
        )

        ai_report = "\n".join(ai_lines)

        final_report = (
            global_report
            + "\n\n"
            + market_report
            + "\n\n"
            + ai_report
        )

        return {
            "engine": "TRINETRA_MARKET",
            "symbol": clean_symbol,
            "market_status": snapshot.get(
                "market_status"
            ),
            "global_health": global_result.get(
                "health"
            ),
            "global_bias": global_result.get(
                "global_bias"
            ),
            "analytics_allowed": snapshot.get(
                "analytics_allowed"
            ),
            "global": global_result,
            "snapshot": snapshot,
            "ai_decision": decision,
            "execution_trace": execution_trace,
            "execution_status": (
                "PARTIAL"
                if failed_stages
                else "COMPLETE"
            ),
            "failed_stages": failed_stages,
            "report": final_report,
        }


if __name__ == "__main__":
    engine = MarketEngine()

    fixture_global = {
        "DOW_JONES": {
            "previous_close": 45000,
            "open": 45050,
            "high": 45200,
            "low": 44900,
            "current": 45150,
            "local_time": "13:30",
            "market_status": "OPEN",
            "why_moving": "Test fixture only.",
            "source": "TEST_FIXTURE",
            "source_confidence": 100,
            "data_status": "LIVE",
        },
        "NASDAQ": {
            "previous_close": 20000,
            "open": 20020,
            "high": 20100,
            "low": 19850,
            "current": 19900,
            "local_time": "13:30",
            "market_status": "OPEN",
            "why_moving": "Test fixture only.",
            "source": "TEST_FIXTURE",
            "source_confidence": 100,
            "data_status": "LIVE",
        },
    }

    result = engine.build(
        "NIFTY",
        global_payloads=fixture_global,
    )

    print(result["report"])



