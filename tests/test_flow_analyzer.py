from __future__ import annotations

import unittest

from src.intelligence.flow_analyzer import FlowAnalyzer
from src.intelligence.institutional_flow import InstitutionalFlow


class TestFlowAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = FlowAnalyzer()

    def test_both_institutions_buying(self) -> None:
        flow = InstitutionalFlow(
            fii_cash=1200.0,
            dii_cash=800.0,
        )

        result = self.analyzer.analyze(flow)

        self.assertEqual(result.fii_bias, "LONG")
        self.assertEqual(result.dii_bias, "LONG")
        self.assertEqual(result.confidence, 85.0)

    def test_both_institutions_selling(self) -> None:
        flow = InstitutionalFlow(
            fii_cash=-1200.0,
            dii_cash=-800.0,
        )

        result = self.analyzer.analyze(flow)

        self.assertEqual(result.fii_bias, "SHORT")
        self.assertEqual(result.dii_bias, "SHORT")
        self.assertEqual(result.confidence, 15.0)

    def test_fii_selling_dii_buying(self) -> None:
        flow = InstitutionalFlow(
            fii_cash=-1000.0,
            dii_cash=700.0,
        )

        result = self.analyzer.analyze(flow)

        self.assertEqual(result.fii_bias, "SHORT")
        self.assertEqual(result.dii_bias, "LONG")
        self.assertEqual(result.confidence, 35.0)

    def test_zero_flow_remains_unknown(self) -> None:
        flow = InstitutionalFlow()

        result = self.analyzer.analyze(flow)

        self.assertEqual(result.fii_bias, "UNKNOWN")
        self.assertEqual(result.dii_bias, "UNKNOWN")
        self.assertEqual(result.confidence, 50.0)

    def test_analyze_returns_same_object(self) -> None:
        flow = InstitutionalFlow(fii_cash=100.0)

        result = self.analyzer.analyze(flow)

        self.assertIs(result, flow)


if __name__ == "__main__":
    unittest.main(verbosity=2)
