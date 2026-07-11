from __future__ import annotations

from typing import Any

from src.pipelines.options_analytics_pipeline import (
    OptionsAnalyticsPipeline,
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
    TRINETRA MARKET orchestration engine.

    Current verified flow:
    Options Pipeline
        → Market Snapshot
        → MARKET Report

    India VIX and FII/DII payloads are dependency inputs.
    Missing inputs are marked NO_DATA and are never fabricated.
    """

    def __init__(
        self,
        options_pipeline: OptionsAnalyticsPipeline | None = None,
        snapshot_engine: MarketSnapshotEngine | None = None,
        report_generator: MarketReportGenerator | None = None,
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
        india_vix_payload: dict[str, Any] | None = None,
        fii_dii_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        clean_symbol = symbol.strip().upper()

        if not clean_symbol:
            raise MarketEngineError(
                "Market symbol cannot be empty."
            )

        options_result = self.options_pipeline.run(
            clean_symbol
        )

        vix_result = (
            india_vix_payload
            if isinstance(india_vix_payload, dict)
            else self._missing_vix_payload()
        )

        flows_result = (
            fii_dii_payload
            if isinstance(fii_dii_payload, dict)
            else self._missing_fii_dii_payload()
        )

        snapshot = self.snapshot_engine.build(
            options_result,
            vix_result,
            flows_result,
        )

        report = self.report_generator.render(
            snapshot
        )

        return {
            "engine": "TRINETRA_MARKET",
            "symbol": clean_symbol,
            "market_status": snapshot.get(
                "market_status"
            ),
            "analytics_allowed": snapshot.get(
                "analytics_allowed"
            ),
            "snapshot": snapshot,
            "report": report,
        }


if __name__ == "__main__":
    engine = MarketEngine()

    result = engine.build("NIFTY")

    print(result["report"])
