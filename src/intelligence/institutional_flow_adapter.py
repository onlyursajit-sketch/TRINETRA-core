from __future__ import annotations

from typing import Any

from src.intelligence.institutional_flow import InstitutionalFlow


class InstitutionalFlowAdapter:
    """Converts FII/DII analysis output into InstitutionalFlow."""

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def from_analysis(
        self,
        payload: dict[str, Any],
    ) -> InstitutionalFlow:
        fii = payload.get("fii") or {}
        dii = payload.get("dii") or {}

        fii_cash = self._number(fii.get("cash_net"))
        dii_cash = self._number(dii.get("cash_net"))

        fii_bias = (
            "LONG"
            if fii_cash > 0
            else "SHORT"
            if fii_cash < 0
            else "UNKNOWN"
        )

        dii_bias = (
            "LONG"
            if dii_cash > 0
            else "SHORT"
            if dii_cash < 0
            else "UNKNOWN"
        )

        return InstitutionalFlow(
            fii_cash=fii_cash,
            dii_cash=dii_cash,
            fii_index_futures=self._number(
                fii.get("index_futures_net")
            ),
            fii_stock_futures=self._number(
                fii.get("stock_futures_net")
            ),
            fii_bias=fii_bias,
            dii_bias=dii_bias,
        )
