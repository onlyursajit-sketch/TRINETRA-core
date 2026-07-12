from __future__ import annotations

import unittest

from src.providers.provider_metrics import ProviderMetrics


class TestProviderMetrics(unittest.TestCase):
    def test_success_metrics(self) -> None:
        metrics = ProviderMetrics()

        metrics.record_success(120.0)
        metrics.record_success(80.0)

        self.assertEqual(metrics.total_calls, 2)
        self.assertEqual(metrics.successful_calls, 2)
        self.assertEqual(metrics.failed_calls, 0)
        self.assertEqual(metrics.average_latency_ms, 100.0)
        self.assertEqual(metrics.success_rate, 100.0)

    def test_failure_metrics(self) -> None:
        metrics = ProviderMetrics()

        metrics.record_success(100.0)
        metrics.record_failure(200.0)

        self.assertEqual(metrics.total_calls, 2)
        self.assertEqual(metrics.successful_calls, 1)
        self.assertEqual(metrics.failed_calls, 1)
        self.assertEqual(metrics.average_latency_ms, 150.0)
        self.assertEqual(metrics.success_rate, 50.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
