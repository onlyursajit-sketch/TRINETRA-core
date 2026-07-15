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

    confidence: float = 0.0
    fii_cash: float = 0.0
    dii_cash: float = 0.0

    fii_index_futures: float = 0.0
    fii_stock_futures: float = 0.0

    fii_bias: str = "UNKNOWN"
    dii_bias: str = "UNKNOWN"
    institutional_confidence: float = 0.0

    regime: str = "UNKNOWN"
