from __future__ import annotations

import tempfile
import unittest

from src.cache.json_cache import JSONCache
from src.market.market_engine import MarketEngine
from src.pipelines.options_analytics_pipeline import (
    OptionsAnalyticsPipeline,
)
from src.providers.option_chain_factory import (
    ManagedOptionChainCollector,
)


class FakeLiveCollectorFailure:
    def collect(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "records": [],
            "source": "NSE",
            "source_confidence": 0,
            "data_status": "NO_DATA",
            "fallback_reason": "Simulated live failure.",
        }


class IntegrationSnapshotEngine:
    def build(
        self,
        options_result: dict,
        vix_result: dict,
        flows_result: dict,
    ) -> dict:
        return {
            "symbol": options_result["symbol"],
            "market_status": "LIVE",
            "analytics_allowed": options_result[
                "analytics_allowed"
            ],
            "source_confidence": 70,
            "confidence": "MEDIUM",
            "institutional_score": 25,
            "warnings": [],
            "option_chain": options_result[
                "option_chain"
            ],
            "oi": options_result["oi"],
            "pcr": options_result["pcr"],
            "max_pain": options_result[
                "max_pain"
            ],
            "india_vix": vix_result,
            "fii_dii": flows_result,
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
    def render(self, payload: dict) -> str:
        return "GLOBAL REPORT"


class TestMarketCacheFallback(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

        self.cache.write(
            "option_chain",
            "nifty",
            {
                "symbol": "NIFTY",
                "source": "NSE",
                "source_confidence": 95,
                "data_status": "LIVE",
                "underlying_value": 25010,
                "nearest_expiry": "17-Jul-2026",
                "atm_strike": 25000,
                "records": [
                    {
                        "strike_price": 24950,
                        "expiry_date": "17-Jul-2026",
                        "ce": {
                            "openInterest": 1000,
                            "changeinOpenInterest": 100,
                            "totalTradedVolume": 500,
                            "lastPrice": 120,
                            "change": 5,
                        },
                        "pe": {
                            "openInterest": 1200,
                            "changeinOpenInterest": 150,
                            "totalTradedVolume": 600,
                            "lastPrice": 60,
                            "change": -4,
                        },
                    },
                    {
                        "strike_price": 25000,
                        "expiry_date": "17-Jul-2026",
                        "ce": {
                            "openInterest": 1800,
                            "changeinOpenInterest": 220,
                            "totalTradedVolume": 900,
                            "lastPrice": 90,
                            "change": -6,
                        },
                        "pe": {
                            "openInterest": 2100,
                            "changeinOpenInterest": 300,
                            "totalTradedVolume": 1100,
                            "lastPrice": 75,
                            "change": 7,
                        },
                    },
                    {
                        "strike_price": 25050,
                        "expiry_date": "17-Jul-2026",
                        "ce": {
                            "openInterest": 2300,
                            "changeinOpenInterest": 350,
                            "totalTradedVolume": 1200,
                            "lastPrice": 70,
                            "change": -5,
                        },
                        "pe": {
                            "openInterest": 1700,
                            "changeinOpenInterest": -180,
                            "totalTradedVolume": 950,
                            "lastPrice": 100,
                            "change": 8,
                        },
                    },
                ],
            },
            ttl_seconds=60,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_cache_fallback_reaches_market_and_ai(
        self,
    ) -> None:
        collector = ManagedOptionChainCollector(
            cache=self.cache,
            collector=FakeLiveCollectorFailure(),
        )

        pipeline = OptionsAnalyticsPipeline(
            collector=collector,
            cache=self.cache,
        )

        engine = MarketEngine(
            options_pipeline=pipeline,
            snapshot_engine=IntegrationSnapshotEngine(),
            report_generator=FakeMarketReportGenerator(),
            global_command_center=FakeGlobalCommandCenter(),
            global_report_generator=FakeGlobalReportGenerator(),
        )

        result = engine.build(
            "NIFTY",
            global_payloads={},
            india_vix_payload={
                "data_status": "LIVE",
                "risk_regime": "LOW",
                "direction": "DOWN",
            },
            fii_dii_payload={
                "data_status": "LIVE",
                "market_bias": "DOMESTICALLY_SUPPORTED",
            },
        )

        option_chain = result["snapshot"][
            "option_chain"
        ]

        self.assertEqual(
            option_chain["provider_used"],
            "JSON_CACHE",
        )

        self.assertTrue(
            option_chain["fallback_used"]
        )

        self.assertIsNotNone(
            result["snapshot"]["oi"]
        )

        self.assertIsNotNone(
            result["snapshot"]["pcr"]
        )

        self.assertIsNotNone(
            result["snapshot"]["max_pain"]
        )

        self.assertIn(
            "ai_decision",
            result,
        )

        self.assertIn(
            result["ai_decision"]["decision"],
            {
                "BUY_BIAS",
                "SELL_BIAS",
                "WAIT",
            },
        )

        self.assertIn(
            "TRINETRA — AI DECISION HUB",
            result["report"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
