from dataclasses import dataclass
from typing import Callable, Optional

from src.models.market_data import MarketData


@dataclass(frozen=True)
class SourceConfig:
    name: str
    priority: int
    confidence: int
    enabled: bool = True


SOURCE_REGISTRY = {
    "NSE": SourceConfig(
        name="NSE",
        priority=1,
        confidence=100,
    ),
    "Dhan": SourceConfig(
        name="Dhan",
        priority=2,
        confidence=98,
    ),
    "Finnhub": SourceConfig(
        name="Finnhub",
        priority=3,
        confidence=85,
    ),
    "AlphaVantage": SourceConfig(
        name="AlphaVantage",
        priority=4,
        confidence=80,
    ),
    "Yahoo": SourceConfig(
        name="Yahoo",
        priority=5,
        confidence=75,
    ),
}


def get_source_config(source_name: str) -> SourceConfig:
    try:
        return SOURCE_REGISTRY[source_name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown source: {source_name}"
        ) from exc


def rank_sources(
    source_names: list[str],
) -> list[str]:
    valid_sources = []

    for source_name in source_names:
        config = get_source_config(source_name)

        if config.enabled:
            valid_sources.append(config)

    valid_sources.sort(
        key=lambda item: item.priority
    )

    return [
        item.name
        for item in valid_sources
    ]


def fetch_with_fallback(
    fetchers: dict[
        str,
        Callable[[], MarketData],
    ],
) -> tuple[
    Optional[MarketData],
    list[str],
]:
    errors = []

    ordered_sources = rank_sources(
        list(fetchers.keys())
    )

    for source_name in ordered_sources:
        fetcher = fetchers[source_name]

        try:
            data = fetcher()

            if data.current is None:
                raise ValueError(
                    "Current price missing."
                )

            return data, errors

        except Exception as exc:
            errors.append(
                f"{source_name}: {exc}"
            )

    return None, errors
