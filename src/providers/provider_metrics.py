from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProviderMetrics:
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_latency_ms: float = 0.0
    last_latency_ms: float | None = None

    def record_success(
        self,
        latency_ms: float,
    ) -> None:
        self.total_calls += 1
        self.successful_calls += 1
        self.total_latency_ms += latency_ms
        self.last_latency_ms = latency_ms

    def record_failure(
        self,
        latency_ms: float,
    ) -> None:
        self.total_calls += 1
        self.failed_calls += 1
        self.total_latency_ms += latency_ms
        self.last_latency_ms = latency_ms

    @property
    def average_latency_ms(self) -> float:
        if self.total_calls == 0:
            return 0.0

        return round(
            self.total_latency_ms / self.total_calls,
            2,
        )

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0

        return round(
            (
                self.successful_calls
                / self.total_calls
            )
            * 100.0,
            2,
        )
