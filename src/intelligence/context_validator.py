from __future__ import annotations

from src.intelligence.market_context import MarketContext


class ContextValidationError(ValueError):
    """Raised when market context contains invalid values."""


class ContextValidator:
    """Validates normalized market-context values."""

    def validate(self, context: MarketContext) -> None:
        if not isinstance(context.symbol, str):
            raise ContextValidationError(
                "Symbol must be a string."
            )

        if not context.symbol.strip():
            raise ContextValidationError(
                "Symbol cannot be empty."
            )

        if context.vix is not None and context.vix < 0:
            raise ContextValidationError(
                "VIX cannot be negative."
            )

        if context.pcr is not None and context.pcr < 0:
            raise ContextValidationError(
                "PCR cannot be negative."
            )

        if context.confidence < 0 or context.confidence > 100:
            raise ContextValidationError(
                "Confidence must be between 0 and 100."
            )

        if (
            context.institutional_confidence < 0
            or context.institutional_confidence > 100
        ):
            raise ContextValidationError(
                "Institutional confidence must be between 0 and 100."
            )
