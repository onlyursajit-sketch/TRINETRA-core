from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TradeSignal:
    action: str
    confidence: float
    risk: float

    regime: str

    fii_bias: str

    pcr: float | None

    max_pain: int | None

    reason: list[str]
