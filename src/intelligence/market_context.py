from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MarketContext:
    symbol: str

    vix: float | None = None
    pcr: float | None = None
    max_pain: int | None = None

    oi_bullish: bool = False
    volume_bullish: bool = False

    fii_bias: str = "UNKNOWN"
    regime: str = "UNKNOWN"

    confidence: float = 0.0
