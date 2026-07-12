from __future__ import annotations

from typing import Any


class GlobalMarketReportError(Exception):
    """Raised when global market report rendering fails."""


class GlobalMarketReportGenerator:
    """
    TRINETRA Global Command Center report renderer.

    Frozen format:
    Market | Previous | Open | High | Low | Current
    | Difference | % | Local Time | Trading Hours
    | Market Status | Why Moving | Source
    """

    @staticmethod
    def _text(
        value: Any,
        default: str = "N/A",
    ) -> str:
        if value is None:
            return default

        cleaned = str(value).strip()
        return cleaned or default

    @staticmethod
    def _number(
        value: Any,
        decimals: int = 2,
    ) -> str:
        if isinstance(value, bool):
            return "N/A"

        try:
            number = float(value)
        except (TypeError, ValueError):
            return "N/A"

        return f"{number:,.{decimals}f}"

    def render(
        self,
        command_center: dict[str, Any],
    ) -> str:
        if not isinstance(command_center, dict):
            raise GlobalMarketReportError(
                "Global Command Center payload must be a dictionary."
            )

        lines = [
            "=" * 90,
            "TRINETRA — GLOBAL COMMAND CENTER",
            "=" * 90,
            f"Health             : "
            f"{self._text(command_center.get('health'))}",
            f"Global Bias        : "
            f"{self._text(command_center.get('global_bias'))}",
            f"Source Confidence  : "
            f"{self._number(command_center.get('source_confidence'))}%",
            f"Generated At       : "
            f"{self._text(command_center.get('generated_at'))}",
            "",
        ]

        summary = command_center.get(
            "summary",
            {},
        )

        if not isinstance(summary, dict):
            summary = {}

        lines.extend(
            [
                "GLOBAL BREADTH",
                "-" * 90,
                f"Total Markets      : "
                f"{self._number(summary.get('total_markets'), 0)}",
                f"Advances           : "
                f"{self._number(summary.get('advances'), 0)}",
                f"Declines           : "
                f"{self._number(summary.get('declines'), 0)}",
                f"Unchanged          : "
                f"{self._number(summary.get('unchanged'), 0)}",
                f"Live               : "
                f"{self._number(summary.get('live'), 0)}",
                f"Stale              : "
                f"{self._number(summary.get('stale'), 0)}",
                f"No Data             : "
                f"{self._number(summary.get('no_data'), 0)}",
                "",
                "GLOBAL MARKETS",
                "-" * 90,
            ]
        )

        markets = command_center.get(
            "markets",
            [],
        )

        if not isinstance(markets, list):
            markets = []

        if not markets:
            lines.append(
                "No verified global market data available."
            )

        for market in markets:
            if not isinstance(market, dict):
                continue

            lines.extend(
                [
                    "",
                    f"{self._text(market.get('country'))} — "
                    f"{self._text(market.get('name'))}",
                    f"Previous Close     : "
                    f"{self._number(market.get('previous_close'))}",
                    f"Open               : "
                    f"{self._number(market.get('open'))}",
                    f"High               : "
                    f"{self._number(market.get('high'))}",
                    f"Low                : "
                    f"{self._number(market.get('low'))}",
                    f"Current            : "
                    f"{self._number(market.get('current'))}",
                    f"Difference         : "
                    f"{self._number(market.get('difference'))}",
                    f"Change %           : "
                    f"{self._number(market.get('percentage_change'), 4)}%",
                    f"Local Time         : "
                    f"{self._text(market.get('local_time'))}",
                    f"Trading Hours      : "
                    f"{self._text(market.get('trading_hours'))}",
                    f"Market Status      : "
                    f"{self._text(market.get('market_status'))}",
                    f"Data Status        : "
                    f"{self._text(market.get('data_status'))}",
                    f"Why Moving         : "
                    f"{self._text(market.get('why_moving'))}",
                    f"Source             : "
                    f"{self._text(market.get('source'))}",
                    f"Source Confidence  : "
                    f"{self._number(market.get('source_confidence'))}%",
                ]
            )

        warnings = command_center.get(
            "warnings",
            [],
        )

        lines.extend(
            [
                "",
                "GLOBAL WARNINGS",
                "-" * 90,
            ]
        )

        if isinstance(warnings, list) and warnings:
            for warning in warnings:
                lines.append(
                    f"- {self._text(warning)}"
                )
        else:
            lines.append("- NONE")

        return "\n".join(lines)
