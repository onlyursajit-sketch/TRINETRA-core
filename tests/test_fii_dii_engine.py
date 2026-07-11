from __future__ import annotations

import unittest

from src.engines.fii_dii_engine import (
    FIIDIIEngine,
    FIIDIIEngineError,
)


BASE_PAYLOAD = {
    "source": "NSE",
    "source_confidence": 100,
    "data_status": "LIVE",
    "trade_date": "2026-07-11",
    "fii": {
        "cash_buy": 12500,
        "cash_sell": 13800,
        "index_futures_net": -750,
        "stock_futures_net": 420,
        "index_options_net": -300,
    },
    "dii": {
        "cash_buy": 11200,
        "cash_sell": 9600,
    },
}


class TestFIIDIIEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = FIIDIIEngine()

    def test_fii_cash_net(self) -> None:
        result = self.engine.analyse(
            BASE_PAYLOAD
        )

        self.assertEqual(
            result["fii"]["cash_net"],
            -1300.0,
        )

    def test_dii_cash_net(self) -> None:
        result = self.engine.analyse(
            BASE_PAYLOAD
        )

        self.assertEqual(
            result["dii"]["cash_net"],
            1600.0,
        )

    def test_combined_cash_net(self) -> None:
        result = self.engine.analyse(
            BASE_PAYLOAD
        )

        self.assertEqual(
            result["combined_cash_net"],
            300.0,
        )

    def test_fii_derivatives_net(self) -> None:
        result = self.engine.analyse(
            BASE_PAYLOAD
        )

        self.assertEqual(
            result["fii"]["derivatives_net"],
            -630.0,
        )

        self.assertEqual(
            result["fii"]["combined_net"],
            -1930.0,
        )

    def test_participant_table_format(self) -> None:
        result = self.engine.analyse(
            BASE_PAYLOAD
        )

        rows = {
            row["participant"]: row
            for row in result["participant_table"]
        }

        self.assertEqual(
            rows["FII"]["position"],
            "NET_SELL",
        )

        self.assertEqual(
            rows["FII"]["amount"],
            -1300.0,
        )

        self.assertEqual(
            rows["FII"]["impact"],
            "BEARISH",
        )

        self.assertEqual(
            rows["DII"]["position"],
            "NET_BUY",
        )

        self.assertEqual(
            rows["DII"]["impact"],
            "DOMESTIC_SUPPORT",
        )

    def test_domestic_support_bias(self) -> None:
        result = self.engine.analyse(
            BASE_PAYLOAD
        )

        self.assertEqual(
            result["flow_structure"],
            "FII_SELL_DII_BUY",
        )

        self.assertEqual(
            result["market_bias"],
            "DOMESTICALLY_SUPPORTED",
        )

    def test_both_buying(self) -> None:
        payload = {
            **BASE_PAYLOAD,
            "fii": {
                **BASE_PAYLOAD["fii"],
                "cash_buy": 15000,
                "cash_sell": 12000,
            },
            "dii": {
                "cash_buy": 11000,
                "cash_sell": 9000,
            },
        }

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["flow_structure"],
            "BOTH_BUYING",
        )

        self.assertEqual(
            result["market_bias"],
            "BULLISH",
        )

    def test_both_selling(self) -> None:
        payload = {
            **BASE_PAYLOAD,
            "fii": {
                **BASE_PAYLOAD["fii"],
                "cash_buy": 10000,
                "cash_sell": 13000,
            },
            "dii": {
                "cash_buy": 8000,
                "cash_sell": 10000,
            },
        }

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["flow_structure"],
            "BOTH_SELLING",
        )

        self.assertEqual(
            result["market_bias"],
            "BEARISH",
        )

    def test_stale_confidence(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["data_status"] = "STALE"

        result = self.engine.analyse(payload)

        self.assertEqual(
            result["confidence"],
            "LOW",
        )

    def test_no_data_blocked(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload["data_status"] = "NO_DATA"

        with self.assertRaises(
            FIIDIIEngineError
        ):
            self.engine.analyse(payload)

    def test_missing_fii_blocked(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload.pop("fii")

        with self.assertRaises(
            FIIDIIEngineError
        ):
            self.engine.analyse(payload)

    def test_missing_dii_blocked(self) -> None:
        payload = dict(BASE_PAYLOAD)
        payload.pop("dii")

        with self.assertRaises(
            FIIDIIEngineError
        ):
            self.engine.analyse(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
