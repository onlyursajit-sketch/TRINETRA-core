from __future__ import annotations

from typing import Any


class MarketReportError(Exception):
    """Raised when market report generation fails."""


class MarketReportGenerator:
    """
    TRINETRA MARKET report renderer.

    Rules:
    - Missing values become N/A
    - No fabricated data
    - Snapshot status and warnings are preserved
    """

    @staticmethod
    def _text(value: Any) -> str:
        if value is None:
            return "N/A"

        cleaned = str(value).strip()
        return cleaned or "N/A"

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

    @staticmethod
    def _section(title: str) -> list[str]:
        return [
            "",
            "=" * 68,
            title,
            "=" * 68,
        ]

    def render(
        self,
        snapshot: dict[str, Any],
    ) -> str:
        if not isinstance(snapshot, dict):
            raise MarketReportError(
                "Snapshot must be a dictionary."
            )

        lines: list[str] = [
            "=" * 68,
            "TRINETRA — MARKET INTELLIGENCE REPORT",
            "=" * 68,
        ]

        lines.extend(
            self._section(
                "EXECUTIVE SUMMARY"
            )
        )

        lines.extend(
            [
                f"Symbol              : "
                f"{self._text(snapshot.get('symbol'))}",
                f"Market Status       : "
                f"{self._text(snapshot.get('market_status'))}",
                f"Market Bias         : "
                f"{self._text(snapshot.get('market_bias'))}",
                f"Institutional Score : "
                f"{self._number(snapshot.get('institutional_score'))}",
                f"Confidence          : "
                f"{self._text(snapshot.get('confidence'))}",
                f"Source Confidence   : "
                f"{self._number(snapshot.get('source_confidence'))}%",
                f"Generated At        : "
                f"{self._text(snapshot.get('generated_at'))}",
            ]
        )

        oi = snapshot.get("oi")
        pcr = snapshot.get("pcr")
        max_pain = snapshot.get("max_pain")
        vix = snapshot.get("india_vix")
        fii_dii = snapshot.get("fii_dii")

        if not isinstance(oi, dict):
            oi = {}

        if not isinstance(pcr, dict):
            pcr = {}

        if not isinstance(max_pain, dict):
            max_pain = {}

        if not isinstance(vix, dict):
            vix = {}

        if not isinstance(fii_dii, dict):
            fii_dii = {}

        lines.extend(
            self._section(
                "OPTIONS INTELLIGENCE"
            )
        )

        lines.extend(
            [
                f"Expiry              : "
                f"{self._text(oi.get('expiry'))}",
                f"ATM Strike          : "
                f"{self._number(oi.get('atm_strike'))}",
                f"Total Call OI       : "
                f"{self._number(oi.get('total_call_oi'), 0)}",
                f"Total Put OI        : "
                f"{self._number(oi.get('total_put_oi'), 0)}",
                f"Call OI Change      : "
                f"{self._number(oi.get('total_call_oi_change'), 0)}",
                f"Put OI Change       : "
                f"{self._number(oi.get('total_put_oi_change'), 0)}",
                f"Support             : "
                f"{self._number(oi.get('support'))}",
                f"Resistance          : "
                f"{self._number(oi.get('resistance'))}",
                f"Overall PCR         : "
                f"{self._number(pcr.get('overall_pcr'), 4)}",
                f"OI Change PCR       : "
                f"{self._number(pcr.get('oi_change_pcr'), 4)}",
                f"ATM PCR             : "
                f"{self._number(pcr.get('atm_pcr'), 4)}",
                f"PCR Bias            : "
                f"{self._text(pcr.get('market_bias'))}",
                f"PCR Signal          : "
                f"{self._text(pcr.get('signal'))}",
                f"Max Pain Strike     : "
                f"{self._number(max_pain.get('max_pain_strike'))}",
                f"Distance from ATM   : "
                f"{self._number(max_pain.get('distance_from_atm'))}",
                f"Distance from Spot  : "
                f"{self._number(max_pain.get('distance_from_underlying'))}",
            ]
        )

        lines.extend(
            self._section(
                "INDIA VIX"
            )
        )

        lines.extend(
            [
                "Previous → Current → Difference → Impact",
                "",
                f"Previous Close      : "
                f"{self._number(vix.get('previous_close'))}",
                f"Current             : "
                f"{self._number(vix.get('current'))}",
                f"Difference          : "
                f"{self._number(vix.get('difference'))}",
                f"Change %            : "
                f"{self._number(vix.get('percentage_change'))}%",
                f"Risk Regime         : "
                f"{self._text(vix.get('risk_regime'))}",
                f"Direction           : "
                f"{self._text(vix.get('direction'))}",
                f"Impact              : "
                f"{self._text(vix.get('impact'))}",
            ]
        )

        lines.extend(
            self._section(
                "FII/DII INTELLIGENCE"
            )
        )

        lines.append(
            "Participant | Position | Amount (₹ Cr) | Impact"
        )
        lines.append("-" * 68)

        participant_table = fii_dii.get(
            "participant_table",
            [],
        )

        if isinstance(participant_table, list) and participant_table:
            for row in participant_table:
                if not isinstance(row, dict):
                    continue

                lines.append(
                    f"{self._text(row.get('participant'))} | "
                    f"{self._text(row.get('position'))} | "
                    f"{self._number(row.get('amount'))} | "
                    f"{self._text(row.get('impact'))}"
                )
        else:
            lines.append(
                "N/A | N/A | N/A | DATA_UNAVAILABLE"
            )

        lines.extend(
            [
                "",
                f"Combined Cash Net   : ₹"
                f"{self._number(fii_dii.get('combined_cash_net'))} Cr",
                f"Flow Structure      : "
                f"{self._text(fii_dii.get('flow_structure'))}",
                f"Market Bias         : "
                f"{self._text(fii_dii.get('market_bias'))}",
                f"Interpretation      : "
                f"{self._text(fii_dii.get('interpretation'))}",
            ]
        )

        lines.extend(
            self._section(
                "INSTITUTIONAL SCORECARD"
            )
        )

        lines.append(
            "Factor | Score | Reason"
        )
        lines.append("-" * 68)

        breakdown = snapshot.get(
            "score_breakdown",
            [],
        )

        if isinstance(breakdown, list) and breakdown:
            for row in breakdown:
                if not isinstance(row, dict):
                    continue

                lines.append(
                    f"{self._text(row.get('factor'))} | "
                    f"{self._number(row.get('score'))} | "
                    f"{self._text(row.get('reason'))}"
                )
        else:
            lines.append(
                "N/A | N/A | Score breakdown unavailable."
            )

        lines.extend(
            self._section(
                "DATA QUALITY & WARNINGS"
            )
        )

        statuses = snapshot.get(
            "source_statuses",
            {},
        )

        if not isinstance(statuses, dict):
            statuses = {}

        lines.extend(
            [
                f"Options Status      : "
                f"{self._text(statuses.get('options'))}",
                f"India VIX Status    : "
                f"{self._text(statuses.get('india_vix'))}",
                f"FII/DII Status      : "
                f"{self._text(statuses.get('fii_dii'))}",
                f"Analytics Allowed   : "
                f"{bool(snapshot.get('analytics_allowed'))}",
                "",
                "Warnings:",
            ]
        )

        warnings = snapshot.get(
            "warnings",
            [],
        )

        if isinstance(warnings, list) and warnings:
            for warning in warnings:
                lines.append(
                    f"- {self._text(warning)}"
                )
        else:
            lines.append("- NONE")

        lines.extend(
            [
                "",
                "TRINETRA Rule:",
                "Verified data + deterministic interpretation only.",
                "No fabricated values and no standalone prediction.",
            ]
        )

        return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(
        "Use MarketReportGenerator.render(snapshot)."
    )
