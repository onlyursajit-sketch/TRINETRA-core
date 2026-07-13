from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InstitutionalFlow:
    fii_cash: float = 0.0
    dii_cash: float = 0.0

    fii_index_futures: float = 0.0
    fii_stock_futures: float = 0.0

    fii_bias: str = "UNKNOWN"
    dii_bias: str = "UNKNOWN"

    confidence: float = 0.0
