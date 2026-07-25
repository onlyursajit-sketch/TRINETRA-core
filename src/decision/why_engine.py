from __future__ import annotations

from typing import Any


class WhyEngine:
    """Build backward-compatible structured decision explanations."""

    @staticmethod
    def _items(messages: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "sequence": index,
                "message": message,
            }
            for index, message in enumerate(messages, start=1)
        ]

    @classmethod
    def build(
        cls,
        *,
        decision: str,
        confidence_score: float,
        reasons: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "decision": decision,
            "confidence_score": confidence_score,
            "causes": cls._items(reasons),
            "warnings": cls._items(warnings),
        }
