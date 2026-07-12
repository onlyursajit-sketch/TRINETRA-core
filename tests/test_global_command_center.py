from __future__ import annotations

import unittest

from src.global_command.global_command_center import (
    GlobalCommandCenter,
    GlobalCommandCenterError,
)


def quote(
    previous: float | None,
    current: float | None,
    status: str = "LIVE",
    confidence: float = 100,
) -> dict:
    return {
        "previous_close": previous,
        "open": previous,
        "high": current,
        "low": previous,
        "current": current,
        "local_time": "12:00",
        "market_status": "OPEN",
        "why_moving": "Test fixture only.",
        "source": "TEST_FIXTURE",
        "source_confidence": confidence,
        "data_status": status,
    }


class TestGlobalCommandCenter(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = GlobalCommandCenter()

    def test_live_global_snapshot(self) -> None:
        result = self.engine.build(
            {
                "DOW_JONES": quote(
                    45000,
                    45100,
                ),
                "NASDAQ": quote(
                    20000,
                    19900,
                ),
            }
        )

        self.assertEqual(
            result["health"],
            "LIVE",
        )

        self.assertEqual(
            result["summary"]["total_markets"],
            2,
        )

        self.assertEqual(
            result["summary"]["live"],
            2,
        )

    def test_breadth_calculation(self) -> None:
        result = self.engine.build(
            {
                "DOW_JONES": quote(
                    45000,
                    45100,
                ),
                "NASDAQ": quote(
                    20000,
                    19900,
                ),
                "NIKKEI225": quote(
                    41000,
                    41200,
                ),
            }
        )

        self.assertEqual(
            result["summary"]["advances"],
            2,
        )

        self.assertEqual(
            result["summary"]["declines"],
            1,
        )

        self.assertEqual(
            result["summary"]["unchanged"],
            0,
        )

        self.assertEqual(
            result["global_bias"],
            "BULLISH",
        )

    def test_canonical_market_order(self) -> None:
        result = self.engine.build(
            {
                "NASDAQ": quote(
                    20000,
                    20100,
                ),
                "DOW_JONES": quote(
                    45000,
                    45100,
                ),
                "SP500": quote(
                    6000,
                    6010,
                ),
            }
        )

        market_ids = [
            market["market_id"]
            for market in result["markets"]
        ]

        self.assertEqual(
            market_ids,
            [
                "DOW_JONES",
                "SP500",
                "NASDAQ",
            ],
        )

    def test_average_source_confidence(self) -> None:
        result = self.engine.build(
            {
                "DOW_JONES": quote(
                    45000,
                    45100,
                    confidence=100,
                ),
                "NASDAQ": quote(
                    20000,
                    20100,
                    confidence=80,
                ),
            }
        )

        self.assertEqual(
            result["source_confidence"],
            90.0,
        )

    def test_partial_health_with_stale_data(self) -> None:
        result = self.engine.build(
            {
                "DOW_JONES": quote(
                    45000,
                    45100,
                    status="LIVE",
                ),
                "NASDAQ": quote(
                    20000,
                    20100,
                    status="STALE",
                ),
            }
        )

        self.assertEqual(
            result["health"],
            "PARTIAL",
        )

        self.assertEqual(
            result["summary"]["stale"],
            1,
        )

        self.assertIn(
            "GLOBAL_DATA_STALE",
            result["warnings"],
        )

    def test_missing_data_warning(self) -> None:
        result = self.engine.build(
            {
                "DOW_JONES": quote(
                    45000,
                    45100,
                ),
                "NASDAQ": quote(
                    None,
                    None,
                ),
            }
        )

        self.assertEqual(
            result["health"],
            "PARTIAL",
        )

        self.assertEqual(
            result["summary"]["no_data"],
            1,
        )

        self.assertIn(
            "GLOBAL_DATA_MISSING",
            result["warnings"],
        )

    def test_all_no_data(self) -> None:
        result = self.engine.build(
            {
                "DOW_JONES": quote(
                    None,
                    None,
                ),
                "NASDAQ": quote(
                    None,
                    None,
                ),
            }
        )

        self.assertEqual(
            result["health"],
            "NO_DATA",
        )

        self.assertEqual(
            result["global_bias"],
            "UNAVAILABLE",
        )

    def test_low_confidence_warning(self) -> None:
        result = self.engine.build(
            {
                "DOW_JONES": quote(
                    45000,
                    45100,
                    confidence=40,
                ),
            }
        )

        self.assertIn(
            "LOW_GLOBAL_SOURCE_CONFIDENCE",
            result["warnings"],
        )

    def test_empty_payload(self) -> None:
        result = self.engine.build({})

        self.assertEqual(
            result["health"],
            "NO_DATA",
        )

        self.assertEqual(
            result["summary"]["total_markets"],
            0,
        )

        self.assertIn(
            "NO_GLOBAL_MARKETS_AVAILABLE",
            result["warnings"],
        )

    def test_invalid_payload_blocked(self) -> None:
        with self.assertRaises(
            GlobalCommandCenterError
        ):
            self.engine.build(
                []  # type: ignore[arg-type]
            )

    def test_unsupported_market_blocked(self) -> None:
        with self.assertRaises(
            GlobalCommandCenterError
        ):
            self.engine.build(
                {
                    "INVALID_MARKET": quote(
                        100,
                        101,
                    )
                }
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
