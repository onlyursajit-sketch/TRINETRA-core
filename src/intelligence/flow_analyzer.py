from __future__ import annotations

from src.intelligence.institutional_flow import InstitutionalFlow


class FlowAnalyzer:
    """Analyzes institutional buying/selling."""

    def analyze(
        self,
        flow: InstitutionalFlow,
    ) -> InstitutionalFlow:

        if flow.fii_cash > 0:
            flow.fii_bias = "LONG"
        elif flow.fii_cash < 0:
            flow.fii_bias = "SHORT"

        if flow.dii_cash > 0:
            flow.dii_bias = "LONG"
        elif flow.dii_cash < 0:
            flow.dii_bias = "SHORT"

        score = 50.0

        if flow.fii_bias == "LONG":
            score += 25
        elif flow.fii_bias == "SHORT":
            score -= 25

        if flow.dii_bias == "LONG":
            score += 10
        elif flow.dii_bias == "SHORT":
            score -= 10

        flow.confidence = max(
            0.0,
            min(100.0, score),
        )

        return flow
