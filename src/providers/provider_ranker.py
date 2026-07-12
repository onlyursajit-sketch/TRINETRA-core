from __future__ import annotations

from dataclasses import dataclass

from src.providers.provider_health import ProviderHealth


@dataclass(frozen=True)
class ProviderRank:
    provider_id: int
    provider_name: str
    original_priority: int
    score: float
    available: bool


class ProviderRanker:
    """
    Ranks providers using health and original priority.

    Higher score means higher preference.
    """

    @staticmethod
    def calculate_score(
        health: ProviderHealth,
        original_priority: int,
    ) -> float:
        if not health.is_available():
            return -1.0

        priority_score = max(
            0.0,
            100.0 - (original_priority * 10.0),
        )

        reliability_score = health.success_rate

        failure_penalty = (
            health.failure_count * 15.0
        )

        return round(
            priority_score
            + reliability_score
            - failure_penalty,
            2,
        )

    def rank(
        self,
        providers: list,
        health_map: dict[int, ProviderHealth],
    ) -> list:
        ranked: list[ProviderRank] = []

        for index, provider in enumerate(providers):
            health = health_map[id(provider)]

            provider_name = getattr(
                provider,
                "name",
                provider.__class__.__name__,
            )

            ranked.append(
                ProviderRank(
                    provider_id=id(provider),
                    provider_name=provider_name,
                    original_priority=index,
                    score=self.calculate_score(
                        health,
                        index,
                    ),
                    available=health.is_available(),
                )
            )

        return sorted(
            ranked,
            key=lambda item: (
                item.available,
                item.score,
                -item.original_priority,
            ),
            reverse=True,
        )
