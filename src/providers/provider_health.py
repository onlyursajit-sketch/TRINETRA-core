from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class ProviderHealth:
    failure_count: int = 0
    success_count: int = 0
    circuit_open_until: datetime | None = None
    last_error: str | None = None
    total_attempts: int = 0
    total_successes: int = 0
    total_failures: int = 0

    def is_available(self) -> bool:
        if self.circuit_open_until is None:
            return True

        now = datetime.now(timezone.utc)

        if now >= self.circuit_open_until:
            self.circuit_open_until = None
            self.failure_count = 0
            return True

        return False

    def record_success(self) -> None:
        self.total_attempts += 1
        self.total_successes += 1
        self.success_count += 1
        self.failure_count = 0
        self.circuit_open_until = None
        self.last_error = None

    def record_failure(
        self,
        error: Exception,
        failure_threshold: int = 3,
        cooldown_seconds: int = 60,
    ) -> None:
        self.total_attempts += 1
        self.total_failures += 1
        self.failure_count += 1
        self.last_error = str(error)

        if self.failure_count >= failure_threshold:
            self.circuit_open_until = (
                datetime.now(timezone.utc)
                + timedelta(seconds=cooldown_seconds)
            )


    @property
    def success_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0

        return round(
            (
                self.total_successes
                / self.total_attempts
            )
            * 100.0,
            2,
        )
