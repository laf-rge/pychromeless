"""
Centralized Decimal utilities for financial calculations.

All monetary values MUST use Decimal, never float.
Import from this module for consistent behavior across the codebase.

Example usage:
    from decimal_utils import TWO_PLACES, ZERO, to_currency, FinancialJsonEncoder

    amount = to_currency("123.45")
    total = ZERO
    json.dumps(data, cls=FinancialJsonEncoder)
"""

import json
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

# Single source of truth for currency precision
TWO_PLACES = Decimal(10) ** -2
ZERO = Decimal("0")


def to_currency(value: str | int | float | Decimal) -> Decimal:
    """
    Convert any numeric value to properly quantized Decimal.

    Always converts via string representation to avoid float precision issues.

    Args:
        value: A numeric value (string, int, float, or Decimal)

    Returns:
        Decimal quantized to 2 decimal places using ROUND_HALF_UP

    Example:
        >>> to_currency("123.456")
        Decimal('123.46')
        >>> to_currency(100)
        Decimal('100.00')
    """
    if isinstance(value, Decimal):
        return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    # Convert via string to avoid float precision issues
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class FinancialJsonEncoder(json.JSONEncoder):
    """
    JSON encoder that preserves Decimal precision via string serialization.

    This encoder converts Decimal to string to preserve exact precision,
    avoiding the precision loss that occurs with float conversion.

    Also handles datetime and date objects.

    Example:
        >>> import json
        >>> from decimal import Decimal
        >>> data = {"amount": Decimal("123.45")}
        >>> json.dumps(data, cls=FinancialJsonEncoder)
        '{"amount": "123.45"}'
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return str(o)  # String preserves exact precision
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)
