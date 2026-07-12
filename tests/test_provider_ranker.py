import unittest

from src.providers.provider_health import ProviderHealth
from src.providers.provider_ranker import ProviderRanker


class Provider:
    def __init__(self, name: str) -> None:
        self.name = name


class TestProviderRanker(unittest.TestCase):
    def test_healthier_provider_ranks_first(self) -> None:
        first = Provider("FIRST")
        second = Provider("SECOND")

        first_health = ProviderHealth()
        second_health = ProviderHealth()

        first_health.record_failure(
            Exception("failure")
        )

        second_health.record_success()

        providers = [first, second]

        health_map = {
            id(first): first_health,
            id(second): second_health,
        }

        ranked = ProviderRanker().rank(
            providers,
            health_map,
        )

        self.assertEqual(
            ranked[0].provider_name,
            "SECOND",
        )

    def test_original_priority_breaks_tie(self) -> None:
        first = Provider("FIRST")
        second = Provider("SECOND")

        providers = [first, second]

        health_map = {
            id(first): ProviderHealth(),
            id(second): ProviderHealth(),
        }

        ranked = ProviderRanker().rank(
            providers,
            health_map,
        )

        self.assertEqual(
            ranked[0].provider_name,
            "FIRST",
        )

    def test_unavailable_provider_ranks_last(self) -> None:
        first = Provider("FIRST")
        second = Provider("SECOND")

        first_health = ProviderHealth()
        second_health = ProviderHealth()

        for _ in range(3):
            first_health.record_failure(
                Exception("failure")
            )

        providers = [first, second]

        health_map = {
            id(first): first_health,
            id(second): second_health,
        }

        ranked = ProviderRanker().rank(
            providers,
            health_map,
        )

        self.assertEqual(
            ranked[-1].provider_name,
            "FIRST",
        )

        self.assertFalse(
            ranked[-1].available
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
