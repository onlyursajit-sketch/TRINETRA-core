from __future__ import annotations

from collections import defaultdict
from typing import Any


class StrikeClusteringError(Exception):
    """Raised when strike clustering cannot be completed."""


class StrikeClusteringEngine:
    """Group option strikes by combined OI and volume strength."""

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return max(0.0, float(value or 0))
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _option_metric(cls, option: Any, *keys: str) -> float:
        if not isinstance(option, dict):
            return 0.0

        for key in keys:
            if key in option:
                return cls._number(option.get(key))

        return 0.0

    def analyse(
        self,
        option_chain: dict[str, Any],
        cluster_size: int = 100,
        top_n: int = 5,
    ) -> dict[str, Any]:
        if not isinstance(option_chain, dict):
            raise StrikeClusteringError(
                "Option-chain payload must be a dictionary."
            )

        if cluster_size <= 0:
            raise StrikeClusteringError(
                "cluster_size must be greater than zero."
            )

        records = option_chain.get("records", [])
        if not isinstance(records, list):
            raise StrikeClusteringError(
                "Option-chain records must be a list."
            )

        buckets: dict[int, dict[str, float]] = defaultdict(
            lambda: {
                "call_oi": 0.0,
                "put_oi": 0.0,
                "call_volume": 0.0,
                "put_volume": 0.0,
                "record_count": 0.0,
            }
        )

        for row in records:
            if not isinstance(row, dict):
                continue

            strike = row.get("strike_price", row.get("strikePrice"))
            try:
                strike_value = float(strike)
            except (TypeError, ValueError):
                continue

            bucket = int(strike_value // cluster_size) * cluster_size
            ce = row.get("ce", row.get("CE", {}))
            pe = row.get("pe", row.get("PE", {}))

            item = buckets[bucket]
            item["call_oi"] += self._option_metric(
                ce,
                "openInterest",
                "open_interest",
                "oi",
            )
            item["put_oi"] += self._option_metric(
                pe,
                "openInterest",
                "open_interest",
                "oi",
            )
            item["call_volume"] += self._option_metric(
                ce,
                "totalTradedVolume",
                "total_traded_volume",
                "volume",
            )
            item["put_volume"] += self._option_metric(
                pe,
                "totalTradedVolume",
                "total_traded_volume",
                "volume",
            )
            item["record_count"] += 1

        clusters: list[dict[str, Any]] = []

        for start_strike, values in buckets.items():
            total_oi = values["call_oi"] + values["put_oi"]
            total_volume = values["call_volume"] + values["put_volume"]
            strength = total_oi + total_volume

            if values["put_oi"] > values["call_oi"]:
                bias = "SUPPORT"
            elif values["call_oi"] > values["put_oi"]:
                bias = "RESISTANCE"
            else:
                bias = "NEUTRAL"

            clusters.append(
                {
                    "cluster_start": start_strike,
                    "cluster_end": start_strike + cluster_size - 1,
                    "call_oi": round(values["call_oi"], 2),
                    "put_oi": round(values["put_oi"], 2),
                    "call_volume": round(values["call_volume"], 2),
                    "put_volume": round(values["put_volume"], 2),
                    "total_oi": round(total_oi, 2),
                    "total_volume": round(total_volume, 2),
                    "strength": round(strength, 2),
                    "bias": bias,
                    "record_count": int(values["record_count"]),
                }
            )

        clusters.sort(
            key=lambda item: item["strength"],
            reverse=True,
        )

        return {
            "cluster_size": cluster_size,
            "cluster_count": len(clusters),
            "top_clusters": clusters[:top_n],
            "strongest_support": next(
                (
                    item
                    for item in clusters
                    if item["bias"] == "SUPPORT"
                ),
                None,
            ),
            "strongest_resistance": next(
                (
                    item
                    for item in clusters
                    if item["bias"] == "RESISTANCE"
                ),
                None,
            ),
        }
