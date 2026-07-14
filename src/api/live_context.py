from __future__ import annotations

from typing import Any

from src.collectors.india_vix_collector import IndiaVIXCollector
from src.providers.option_chain_factory import ManagedOptionChainCollector


option_chain_collector = ManagedOptionChainCollector()
vix_collector = IndiaVIXCollector()


def build_live_context(builder: Any, symbol: str) -> Any:
    """
    Collects available live/fallback market data and builds MarketContext.

    Provider failures are isolated so the API still returns a neutral context
    instead of crashing.
    """
    options_result: dict[str, Any] | None = None
    vix_payload: dict[str, Any] | None = None

    try:
        options_result = option_chain_collector.collect(symbol)
    except Exception:
        options_result = None

    try:
        vix_payload = vix_collector.collect()
    except Exception:
        vix_payload = None

    try:
        return builder.build(
            symbol=symbol,
            options_result=options_result,
            vix_payload=vix_payload,
        )
    except TypeError:
        # Compatibility for lightweight/fake builders used by API tests.
        return builder.build(symbol=symbol)
