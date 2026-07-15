from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.cache.json_cache import JSONCache, JSONCacheError
from src.collectors.nse_option_chain import NSEOptionChainCollector
from src.providers.option_chain_factory import (
    ManagedOptionChainCollector,
)
from src.engines.max_pain_engine import (
    MaxPainEngine,
    MaxPainEngineError,
)
from src.engines.oi_engine import OIEngine, OIEngineError
from src.engines.pcr_engine import PCREngine, PCREngineError
from src.engines.volume_analysis_engine import (
    VolumeAnalysisEngine,
    VolumeAnalysisError,
)
from src.engines.strike_clustering_engine import (
    StrikeClusteringEngine,
    StrikeClusteringError,
)


class OptionsAnalyticsPipelineError(Exception):
    """Raised when the options analytics pipeline fails unexpectedly."""


class OptionsAnalyticsPipeline:
    """
    TRINETRA unified options analytics pipeline.

    Flow:
    Collector → OI → PCR → Max Pain → JSON Cache

    Rules:
    - NO_DATA blocks analytics.
    - STALE data is allowed with warnings.
    - Each module result is cached independently.
    - No fabricated data is generated.
    """

    DEFAULT_TTL_SECONDS = {
        "option_chain": 300,
        "oi": 300,
        "pcr": 300,
        "max_pain": 300,
        "volume_analysis": 300,
        "strike_clusters": 300,
        "snapshot": 300,
    }

    def __init__(
        self,
        collector: Any | None = None,
        oi_engine: OIEngine | None = None,
        pcr_engine: PCREngine | None = None,
        max_pain_engine: MaxPainEngine | None = None,
        cache: JSONCache | None = None,
        volume_analysis_engine: VolumeAnalysisEngine | None = None,
        strike_clustering_engine: StrikeClusteringEngine | None = None,
    ) -> None:
        self.collector = (
            collector
            or ManagedOptionChainCollector(
                cache=cache
            )
        )
        self.oi_engine = oi_engine or OIEngine()
        self.pcr_engine = pcr_engine or PCREngine()
        self.max_pain_engine = max_pain_engine or MaxPainEngine()
        self.volume_analysis_engine = (
            volume_analysis_engine or VolumeAnalysisEngine()
        )
        self.strike_clustering_engine = (
            strike_clustering_engine or StrikeClusteringEngine()
        )
        self.cache = cache or JSONCache()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _cache_key(symbol: str) -> str:
        return symbol.strip().lower()

    def _write_cache(
        self,
        namespace: str,
        key: str,
        payload: dict[str, Any],
    ) -> str | None:
        ttl_seconds = self.DEFAULT_TTL_SECONDS.get(namespace)

        try:
            path = self.cache.write(
                namespace=namespace,
                key=key,
                payload=payload,
                ttl_seconds=ttl_seconds,
            )
            return str(path)

        except JSONCacheError:
            return None

    def run(
        self,
        symbol: str = "NIFTY",
        expiry: str | None = None,
    ) -> dict[str, Any]:
        clean_symbol = symbol.strip().upper()
        cache_key = self._cache_key(clean_symbol)

        started_at = self._utc_now()

        option_chain = self.collector.collect(clean_symbol)

        option_chain_cache_path = self._write_cache(
            "option_chain",
            cache_key,
            option_chain,
        )

        if option_chain.get("data_status") == "NO_DATA":
            snapshot = {
                "pipeline": "OPTIONS_ANALYTICS",
                "symbol": clean_symbol,
                "data_status": "NO_DATA",
                "started_at": started_at,
                "completed_at": self._utc_now(),
                "option_chain": option_chain,
                "oi": None,
                "pcr": None,
                "max_pain": None,
                "volume_analysis": None,
                "strike_clusters": None,
                "analytics_allowed": False,
                "errors": [
                    option_chain.get(
                        "fallback_reason",
                        "Option-chain data unavailable.",
                    )
                ],
                "cache_paths": {
                    "option_chain": option_chain_cache_path,
                    "oi": None,
                    "pcr": None,
                    "max_pain": None,
                    "volume_analysis": None,
                    "strike_clusters": None,
                    "snapshot": None,
                },
            }

            snapshot_path = self._write_cache(
                "snapshot",
                cache_key,
                snapshot,
            )

            snapshot["cache_paths"]["snapshot"] = snapshot_path
            return snapshot

        errors: list[str] = []

        oi_result: dict[str, Any] | None = None
        pcr_result: dict[str, Any] | None = None
        max_pain_result: dict[str, Any] | None = None
        volume_analysis_result: dict[str, Any] | None = None
        strike_clusters_result: dict[str, Any] | None = None

        oi_cache_path: str | None = None
        pcr_cache_path: str | None = None
        max_pain_cache_path: str | None = None
        volume_analysis_cache_path: str | None = None
        strike_clusters_cache_path: str | None = None

        try:
            oi_result = self.oi_engine.analyse(
                option_chain,
                expiry=expiry,
            )

            oi_cache_path = self._write_cache(
                "oi",
                cache_key,
                oi_result,
            )

        except OIEngineError as exc:
            errors.append(f"OI_ENGINE: {exc}")

        if oi_result is not None:
            try:
                pcr_result = self.pcr_engine.analyse(
                    oi_result
                )

                pcr_cache_path = self._write_cache(
                    "pcr",
                    cache_key,
                    pcr_result,
                )

            except PCREngineError as exc:
                errors.append(f"PCR_ENGINE: {exc}")

        try:
            max_pain_result = self.max_pain_engine.analyse(
                option_chain,
                expiry=expiry,
            )

            max_pain_cache_path = self._write_cache(
                "max_pain",
                cache_key,
                max_pain_result,
            )

        except MaxPainEngineError as exc:
            errors.append(f"MAX_PAIN_ENGINE: {exc}")

        try:
            volume_analysis_result = self.volume_analysis_engine.analyse(
                option_chain,
            )
            volume_analysis_cache_path = self._write_cache(
                "volume_analysis",
                cache_key,
                volume_analysis_result,
            )
        except VolumeAnalysisError as exc:
            errors.append(f"VOLUME_ANALYSIS_ENGINE: {exc}")

        try:
            strike_clusters_result = self.strike_clustering_engine.analyse(
                option_chain,
            )
            strike_clusters_cache_path = self._write_cache(
                "strike_clusters",
                cache_key,
                strike_clusters_result,
            )
        except StrikeClusteringError as exc:
            errors.append(f"STRIKE_CLUSTERING_ENGINE: {exc}")

        analytics_allowed = (
            oi_result is not None
            and pcr_result is not None
            and max_pain_result is not None
            and volume_analysis_result is not None
            and strike_clusters_result is not None
        )

        pipeline_status = (
            option_chain.get("data_status", "UNKNOWN")
            if analytics_allowed
            else "PARTIAL"
        )

        snapshot = {
            "pipeline": "OPTIONS_ANALYTICS",
            "symbol": clean_symbol,
            "data_status": pipeline_status,
            "started_at": started_at,
            "completed_at": self._utc_now(),
            "option_chain": option_chain,
            "oi": oi_result,
            "pcr": pcr_result,
            "max_pain": max_pain_result,
            "volume_analysis": volume_analysis_result,
            "strike_clusters": strike_clusters_result,
            "analytics_allowed": analytics_allowed,
            "errors": errors,
            "cache_paths": {
                "option_chain": option_chain_cache_path,
                "oi": oi_cache_path,
                "pcr": pcr_cache_path,
                "max_pain": max_pain_cache_path,
                "volume_analysis": volume_analysis_cache_path,
                "strike_clusters": strike_clusters_cache_path,
                "snapshot": None,
            },
        }

        snapshot_path = self._write_cache(
            "snapshot",
            cache_key,
            snapshot,
        )

        snapshot["cache_paths"]["snapshot"] = snapshot_path

        return snapshot


if __name__ == "__main__":
    pipeline = OptionsAnalyticsPipeline()

    result = pipeline.run("NIFTY")

    print("=" * 65)
    print("TRINETRA - OPTIONS ANALYTICS PIPELINE")
    print("=" * 65)
    print(f"Symbol             : {result['symbol']}")
    print(f"Data Status        : {result['data_status']}")
    print(f"Analytics Allowed  : {result['analytics_allowed']}")

    if result["oi"] is not None:
        print(
            f"Total Call OI      : "
            f"{result['oi']['total_call_oi']}"
        )
        print(
            f"Total Put OI       : "
            f"{result['oi']['total_put_oi']}"
        )
        print(
            f"Support            : "
            f"{result['oi']['support']}"
        )
        print(
            f"Resistance         : "
            f"{result['oi']['resistance']}"
        )

    if result["pcr"] is not None:
        print(
            f"Overall PCR        : "
            f"{result['pcr']['overall_pcr']}"
        )
        print(
            f"PCR Bias           : "
            f"{result['pcr']['market_bias']}"
        )

    if result["max_pain"] is not None:
        print(
            f"Max Pain           : "
            f"{result['max_pain']['max_pain_strike']}"
        )

    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")

    print(
        f"Snapshot Cache     : "
        f"{result['cache_paths']['snapshot']}"
    )
