from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class MarketData:
    symbol: str
    display_name: str
    asset_class: str
    exchange: Optional[str]
    currency: Optional[str]

    previous_close: Optional[float]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    current: Optional[float]

    change: Optional[float]
    change_percent: Optional[float]
    volume: Optional[int]

    timestamp: Optional[str]
    market_state: str
    source: str
    data_state: str
    confidence: int

    def to_dict(self) -> dict:
        return asdict(self)

    def compact_price(self) -> str:
        if self.current is None:
            return "N/A"

        if self.asset_class == "forex":
            return f"{self.current:,.4f}"

        return f"{self.current:,.0f}"

    def detailed_price(self) -> str:
        if self.current is None:
            return "N/A"

        return f"{self.current:,.2f}"
