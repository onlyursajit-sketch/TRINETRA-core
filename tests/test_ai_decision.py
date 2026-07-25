from __future__ import annotations

import unittest

from src.decision.ai_decision import (
    AIDecisionError,
    AIDecisionHub,
)


def make_market_result(
    global_bias: str = "BULLISH",
    global_confidence: float = 90,
    market_status: str = "LIVE",
    analytics_allowed: bool = True,
    source_confidence: float = 90,
    snapshot_confidence: str = "HIGH",
    institutional_score: float = 40,
    pcr: float = 1.08,
    vix_regime: str = "LOW",
    vix_direction: str = "DOWN",
    flow_bias: str = "DOMESTICALLY_SUPPORTED",
) -> dict:
    return {
        "global": {
            "global_bias": global_bias,
            "source_confidence": global_confidence,
            "warnings": [],
        },
        "snapshot": {
            "market_status": market_status,
            "analytics_allowed": analytics_allowed,
            "source_confidence": source_confidence,
            "confidence": snapshot_confidence,
            "institutional_score": institutional_score,
            "warnings": [],
            "pcr": {
                "overall_pcr": pcr,
            },
            "india_vix": {
                "risk_regime": vix_regime,
                "direction": vix_direction,
            },
            "fii_dii": {
                "market_bias": flow_bias,
            },
        },
    }


class TestAIDecisionHub(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = AIDecisionHub()

    def test_bullish_alignment(self) -> None:
        result = self.engine.decide(
            make_market_result()
        )

        self.assertEqual(
            result["decision"],
            "BUY_BIAS",
        )

        self.assertEqual(
            result["action"],
            "WAIT_FOR_LONG_CONFIRMATION",
        )

        self.assertEqual(
            result["risk"],
            "LOW",
        )

    def test_bearish_alignment(self) -> None:
        result = self.engine.decide(
            make_market_result(
                global_bias="STRONG_BEARISH",
                institutional_score=-45,
                pcr=0.70,
                vix_regime="HIGH",
                vix_direction="UP",
                flow_bias="FII_SELLING_DOMINANT",
            )
        )

        self.assertEqual(
            result["decision"],
            "SELL_BIAS",
        )

        self.assertEqual(
            result["action"],
            "WAIT_FOR_SHORT_CONFIRMATION",
        )

        self.assertIn(
            result["risk"],
            {"MEDIUM", "HIGH"},
        )

    def test_neutral_alignment(self) -> None:
        result = self.engine.decide(
            make_market_result(
                global_bias="NEUTRAL",
                institutional_score=0,
                pcr=0.95,
                flow_bias="UNAVAILABLE",
            )
        )

        self.assertEqual(
            result["decision"],
            "WAIT",
        )

        self.assertEqual(
            result["action"],
            "WAIT",
        )

    def test_no_data_blocks_trade(self) -> None:
        result = self.engine.decide(
            make_market_result(
                market_status="NO_DATA",
                analytics_allowed=False,
                source_confidence=0,
                global_confidence=0,
                snapshot_confidence="NONE",
            )
        )

        self.assertEqual(
            result["decision"],
            "NO_TRADE",
        )

        self.assertEqual(
            result["action"],
            "WAIT_FOR_VERIFIED_DATA",
        )

        self.assertEqual(
            result["confidence"],
            "NONE",
        )

    def test_low_confidence_blocks_trade(self) -> None:
        result = self.engine.decide(
            make_market_result(
                source_confidence=40,
                global_confidence=40,
            )
        )

        self.assertEqual(
            result["decision"],
            "NO_TRADE",
        )

        self.assertIn(
            "Combined source confidence is below 50%.",
            result["reasons"],
        )

    def test_high_vix_warning(self) -> None:
        result = self.engine.decide(
            make_market_result(
                vix_regime="HIGH",
                vix_direction="UP",
            )
        )

        self.assertIn(
            "HIGH_VOLATILITY",
            result["warnings"],
        )

    def test_extreme_vix_warning(self) -> None:
        result = self.engine.decide(
            make_market_result(
                vix_regime="EXTREME",
                vix_direction="UP",
            )
        )

        self.assertIn(
            "EXTREME_VOLATILITY",
            result["warnings"],
        )

    def test_crowded_pcr_warning(self) -> None:
        result = self.engine.decide(
            make_market_result(
                pcr=1.70,
            )
        )

        self.assertIn(
            "CROWDED_PCR_POSITIONING",
            result["warnings"],
        )

    def test_invalid_input_blocked(self) -> None:
        with self.assertRaises(
            AIDecisionError
        ):
            self.engine.decide(
                []  # type: ignore[arg-type]
            )

    def test_score_clamped(self) -> None:
        result = self.engine.decide(
            make_market_result(
                global_bias="STRONG_BULLISH",
                institutional_score=100,
                pcr=1.10,
                flow_bias="BULLISH",
            )
        )

        self.assertLessEqual(
            result["score"],
            100.0,
        )

    def test_risk_clamped(self) -> None:
        result = self.engine.decide(
            make_market_result(
                vix_regime="EXTREME",
                vix_direction="UP",
            )
        )

        self.assertLessEqual(
            result["risk_score"],
            100.0,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)


def test_decision_includes_trade_quality_score() -> None:
    from src.decision.ai_decision import AIDecisionHub

    snapshot = {
        "source_confidence": 90,
        "confidence": "HIGH",
        "analytics_allowed": True,
        "market_status": "LIVE",
        "global": {
            "source_confidence": 90,
            "bias": "BULLISH",
        },
        "institutional": {
            "market_bias": "BULLISH",
        },
        "vix": {
            "risk_regime": "LOW",
        },
    }

    result = AIDecisionHub().decide(snapshot)

    assert "trade_quality_score" in result
    assert 0.0 <= result["trade_quality_score"] <= 100.0


def test_decision_includes_structured_explanation() -> None:
    from src.decision.ai_decision import AIDecisionHub

    snapshot = {
        "source_confidence": 90,
        "confidence": "HIGH",
        "analytics_allowed": True,
        "market_status": "LIVE",
        "global": {
            "source_confidence": 90,
            "bias": "BULLISH",
        },
        "institutional": {
            "market_bias": "BULLISH",
        },
        "vix": {
            "risk_regime": "LOW",
        },
    }

    result = AIDecisionHub().decide(snapshot)

    assert "explanation" in result
    assert result["explanation"]["summary"]
    assert result["explanation"]["reasons"] == result["reasons"]
    assert result["explanation"]["warnings"] == result["warnings"]

def test_decision_uses_oi_and_volume_bias() -> None:
    from src.decision.ai_decision import AIDecisionHub

    hub = AIDecisionHub()

    result = hub.decide({
        "snapshot": {
            "market_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "confidence": "HIGH",
            "institutional_score": 0,
            "oi": {
                "market_bias": "BULLISH",
            },
            "volume_analysis": {
                "market_bias": "BULLISH",
            },
        },
        "global": {
            "source_confidence": 90,
            "global_bias": "NEUTRAL",
        },
    })

    assert result["score"] > 0
    assert any(
        "open interest" in reason.lower()
        for reason in result["explanation"]["reasons"]
    )
    assert any(
        "volume" in reason.lower()
        for reason in result["explanation"]["reasons"]
    )

def test_decision_uses_max_pain_context() -> None:
    from src.decision.ai_decision import AIDecisionHub

    hub = AIDecisionHub()

    result = hub.decide({
        "snapshot": {
            "market_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "confidence": "HIGH",
            "institutional_score": 0,
            "max_pain": {
                "max_pain_strike": 25000,
                "spot_price": 25100,
            },
        },
        "global": {
            "source_confidence": 90,
            "global_bias": "NEUTRAL",
        },
    })

    assert any(
        "max pain" in reason.lower()
        for reason in result["explanation"]["reasons"]
    )

def test_decision_uses_strike_cluster_context() -> None:
    from src.decision.ai_decision import AIDecisionHub

    result = AIDecisionHub().decide({
        "snapshot": {
            "market_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "confidence": "HIGH",
            "institutional_score": 0,
            "strike_clusters": {
                "cluster_count": 2,
                "strongest_support": {
                    "cluster_start": 25000,
                    "cluster_end": 25099,
                    "bias": "SUPPORT",
                    "strength": 1500,
                },
                "strongest_resistance": {
                    "cluster_start": 25300,
                    "cluster_end": 25399,
                    "bias": "RESISTANCE",
                    "strength": 1200,
                },
                "top_clusters": [],
            },
        },
        "global": {
            "source_confidence": 90,
            "global_bias": "NEUTRAL",
        },
    })

    reasons = result["explanation"]["reasons"]

    assert any(
        "support" in reason.lower()
        for reason in reasons
    )
    assert any(
        "resistance" in reason.lower()
        for reason in reasons
    )

def test_decision_scores_strong_strike_cluster_support() -> None:
    from src.decision.ai_decision import AIDecisionHub

    result = AIDecisionHub().decide({
        "snapshot": {
            "market_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "confidence": "HIGH",
            "institutional_score": 0,
            "strike_clusters": {
                "cluster_count": 2,
                "strongest_support": {
                    "cluster_start": 25000,
                    "cluster_end": 25099,
                    "bias": "SUPPORT",
                    "strength": 1800,
                },
                "strongest_resistance": None,
                "top_clusters": [],
            },
        },
        "global": {
            "source_confidence": 90,
            "global_bias": "NEUTRAL",
        },
    })

    assert result["score"] > 0

def test_decision_scores_strong_strike_cluster_resistance() -> None:
    from src.decision.ai_decision import AIDecisionHub

    result = AIDecisionHub().decide({
        "snapshot": {
            "market_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "confidence": "HIGH",
            "institutional_score": 0,
            "strike_clusters": {
                "cluster_count": 2,
                "strongest_support": None,
                "strongest_resistance": {
                    "cluster_start": 25300,
                    "cluster_end": 25399,
                    "bias": "RESISTANCE",
                    "strength": 1800,
                },
                "top_clusters": [],
            },
        },
        "global": {
            "source_confidence": 90,
            "global_bias": "NEUTRAL",
        },
    })

    assert result["score"] < 0
    assert any(
        "resistance" in reason.lower()
        for reason in result["explanation"]["reasons"]
    )

def test_decision_rewards_bullish_multi_signal_confluence() -> None:
    from src.decision.ai_decision import AIDecisionHub

    result = AIDecisionHub().decide({
        "snapshot": {
            "market_status": "LIVE",
            "analytics_allowed": True,
            "source_confidence": 90,
            "confidence": "HIGH",
            "institutional_score": 0,
            "pcr": {
                "overall_pcr": 1.10,
                "market_bias": "BULLISH",
            },
            "oi": {
                "market_bias": "BULLISH",
            },
            "volume_analysis": {
                "market_bias": "BULLISH",
            },
            "strike_clusters": {
                "cluster_count": 1,
                "strongest_support": {
                    "cluster_start": 25000,
                    "cluster_end": 25099,
                    "bias": "SUPPORT",
                    "strength": 1800,
                },
                "strongest_resistance": None,
                "top_clusters": [],
            },
        },
        "global": {
            "source_confidence": 90,
            "global_bias": "NEUTRAL",
        },
    })

    assert result["score"] >= 30
    assert any(
        "confluence" in reason.lower()
        for reason in result["explanation"]["reasons"]
    )

