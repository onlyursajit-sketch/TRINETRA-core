from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.cache.json_cache import JSONCache
from src.snapshot.market_snapshot import (
    MarketSnapshotEngine,
    MarketSnapshotError,
)


def make_options(
    status: str = "LIVE",
    analytics_allowed: bool = True,
) -> dict:
    return {
        "symbol": "NIFTY",
        "data_status": status,
        "analytics_allowed": analytics_allowed,
        "errors": [],
        "option_chain": {
            "source": "NSE",
            "source_confidence": 100,
            "data_status": status,
        },
        "oi": {
            "total_call_oi_change": 500,
            "total_put_oi_change": 900,
        },
        "pcr": {
            "overall_pcr": 1.08,
        },
        "max_pain": {
            "underlying_value": 25050,
            "max_pain_strike": 25000,
        },
    }


def make_vix(
    status: str = "LIVE",
    confidence: float = 100,
) -> dict:
    return {
        "source": "NSE",
        "source_confidence": confidence,
        "data_status": status,
        "current": 14.5,
        "risk_regime": "LOW",
        "direction": "DOWN",
    }


def make_flows(
    status: str = "LIVE",
    confidence: float = 100,
) -> dict:
    return {
        "source": "NSE",
        "source_confidence": confidence,
        "data_status": status,
        "market_bias": "DOMESTICALLY_SUPPORTED",
        "fii": {
            "cash_net": -500,
        },
    }


class TestMarketSnapshotEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.cache = JSONCache(
            base_dir=self.temp_dir.name
        )

        self.engine = MarketSnapshotEngine(
            cache=self.cache,
            snapshot_ttl_seconds=300,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_live_snapshot(self) -> None:
        result = self.engine.build(
            make_options(),
            make_vix(),
            make_flows(),
        )

        self.assertEqual(
            result["market_status"],
            "LIVE",
        )

        self.assertEqual(
            result["confidence"],
            "HIGH",
        )

        self.assertTrue(
            result["analytics_allowed"]
        )

    def test_expected_score(self) -> None:
        result = self.engine.build(
            make_options(),
            make_vix(),
            make_flows(),
        )

        self.assertEqual(
            result["institutional_score"],
            58.0,
        )

        self.assertEqual(
            result["market_bias"],
            "BULLISH",
        )

    def test_source_confidence_average(self) -> None:
        result = self.engine.build(
            make_options(),
            make_vix(),
            make_flows(),
        )

        self.assertEqual(
            result["source_confidence"],
            100.0,
        )

    def test_fii_selling_warning(self) -> None:
        result = self.engine.build(
            make_options(),
            make_vix(),
            make_flows(),
        )

        self.assertIn(
            "FII_SELLING",
            result["warnings"],
        )

    def test_stale_status(self) -> None:
        result = self.engine.build(
            make_options(),
            make_vix(status="STALE"),
            make_flows(),
        )

        self.assertEqual(
            result["market_status"],
            "STALE",
        )

        self.assertEqual(
            result["confidence"],
            "MEDIUM",
        )

        self.assertIn(
            "STALE_DATA",
            result["warnings"],
        )

    def test_partial_status(self) -> None:
        result = self.engine.build(
            make_options(),
            make_vix(status="NO_DATA"),
            make_flows(),
        )

        self.assertEqual(
            result["market_status"],
            "PARTIAL",
        )

        self.assertEqual(
            result["confidence"],
            "LOW",
        )

        self.assertIn(
            "INDIA_VIX_UNAVAILABLE",
            result["warnings"],
        )

    def test_all_no_data(self) -> None:
        result = self.engine.build(
            make_options(
                status="NO_DATA",
                analytics_allowed=False,
            ),
            make_vix(status="NO_DATA"),
            make_flows(status="NO_DATA"),
        )

        self.assertEqual(
            result["market_status"],
            "NO_DATA",
        )

        self.assertEqual(
            result["confidence"],
            "NONE",
        )

        self.assertEqual(
            result["institutional_score"],
            0.0,
        )

        self.assertEqual(
            result["market_bias"],
            "UNAVAILABLE",
        )

        self.assertFalse(
            result["analytics_allowed"]
        )

        self.assertIn(
            "NO_DATA",
            result["warnings"],
        )

        self.assertIn(
            "NO_DECISION_CONFIDENCE",
            result["warnings"],
        )

    def test_low_source_confidence_warning(self) -> None:
        options = make_options()
        options["option_chain"][
            "source_confidence"
        ] = 40

        result = self.engine.build(
            options,
            make_vix(confidence=40),
            make_flows(confidence=40),
        )

        self.assertEqual(
            result["source_confidence"],
            40.0,
        )

        self.assertIn(
            "LOW_SOURCE_CONFIDENCE",
            result["warnings"],
        )

    def test_high_vix_warning(self) -> None:
        vix = make_vix()
        vix["risk_regime"] = "HIGH"
        vix["direction"] = "UP"

        result = self.engine.build(
            make_options(),
            vix,
            make_flows(),
        )

        self.assertIn(
            "HIGH_VIX",
            result["warnings"],
        )

    def test_low_pcr_warning(self) -> None:
        options = make_options()
        options["pcr"]["overall_pcr"] = 0.70

        result = self.engine.build(
            options,
            make_vix(),
            make_flows(),
        )

        self.assertIn(
            "LOW_PCR",
            result["warnings"],
        )

    def test_high_pcr_warning(self) -> None:
        options = make_options()
        options["pcr"]["overall_pcr"] = 1.30

        result = self.engine.build(
            options,
            make_vix(),
            make_flows(),
        )

        self.assertIn(
            "HIGH_PCR",
            result["warnings"],
        )

    def test_snapshot_cache_created(self) -> None:
        result = self.engine.build(
            make_options(),
            make_vix(),
            make_flows(),
        )

        self.assertIsNotNone(
            result["cache_path"]
        )

        assert result["cache_path"] is not None

        self.assertTrue(
            Path(result["cache_path"]).exists()
        )

    def test_invalid_options_payload_blocked(self) -> None:
        with self.assertRaises(
            MarketSnapshotError
        ):
            self.engine.build(
                [],  # type: ignore[arg-type]
                make_vix(),
                make_flows(),
            )

    def test_negative_ttl_blocked(self) -> None:
        with self.assertRaises(
            MarketSnapshotError
        ):
            MarketSnapshotEngine(
                cache=self.cache,
                snapshot_ttl_seconds=-1,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)


def test_snapshot_exposes_structured_data_quality() -> None:
    result = MarketSnapshotEngine().build(
        {
            "symbol": "NIFTY",
            "data_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "errors": [],
            "option_chain": {},
            "oi": {},
            "pcr": {},
            "max_pain": {},
        },
        {
            "data_status": "STALE",
            "source_confidence": 70,
            "risk_regime": "HIGH",
        },
        {
            "data_status": "LIVE",
            "source_confidence": 80,
            "market_bias": "NEUTRAL",
        },
    )

    data_quality = result["data_quality"]

    assert data_quality["overall_status"] == result["data_status"]
    assert (
        data_quality["source_confidence"]
        == result["source_confidence"]
    )
    assert data_quality["confidence_label"] == result["confidence"]
    assert (
        data_quality["analytics_allowed"]
        == result["analytics_allowed"]
    )
    assert data_quality["source_statuses"] == result["source_statuses"]
    assert data_quality["warnings"] == result["warnings"]


def test_snapshot_exposes_source_confidence_breakdown() -> None:
    result = MarketSnapshotEngine().build(
        {
            "symbol": "NIFTY",
            "data_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "errors": [],
            "option_chain": {},
            "oi": {},
            "pcr": {},
            "max_pain": {},
        },
        {
            "data_status": "LIVE",
            "source_confidence": 70,
            "risk_regime": "LOW",
        },
        {
            "data_status": "LIVE",
            "source_confidence": 80,
            "market_bias": "NEUTRAL",
        },
    )

    assert result["data_quality"]["confidence_sources"] == {
        "options": 90.0,
        "india_vix": 70.0,
        "fii_dii": 80.0,
        "valid_source_count": 3,
        "average": 80.0,
    }


def test_snapshot_excludes_invalid_source_confidence_values() -> None:
    result = MarketSnapshotEngine().build(
        {
            "symbol": "NIFTY",
            "data_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 150,
            "errors": [],
            "option_chain": {},
            "oi": {},
            "pcr": {},
            "max_pain": {},
        },
        {
            "data_status": "LIVE",
            "source_confidence": -10,
            "risk_regime": "LOW",
        },
        {
            "data_status": "LIVE",
            "source_confidence": 80,
            "market_bias": "NEUTRAL",
        },
    )

    confidence_sources = result["data_quality"]["confidence_sources"]

    assert confidence_sources["options"] is None
    assert confidence_sources["india_vix"] is None
    assert confidence_sources["fii_dii"] == 80.0
    assert confidence_sources["valid_source_count"] == 1
    assert confidence_sources["average"] == 80.0


def test_snapshot_exposes_data_quality_degradation_reasons() -> None:
    result = MarketSnapshotEngine().build(
        {
            "symbol": "NIFTY",
            "data_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "errors": [],
            "option_chain": {},
            "oi": {},
            "pcr": {},
            "max_pain": {},
        },
        {
            "data_status": "STALE",
            "source_confidence": 70,
            "risk_regime": "HIGH",
        },
        {
            "data_status": "NO_DATA",
            "source_confidence": 0,
            "market_bias": "UNAVAILABLE",
        },
    )

    assert result["data_quality"]["degraded_sources"] == [
        {
            "source": "india_vix",
            "status": "STALE",
        },
        {
            "source": "fii_dii",
            "status": "NO_DATA",
        },
    ]
