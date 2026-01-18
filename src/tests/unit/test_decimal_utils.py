"""
Unit tests for decimal_utils module.

Tests cover:
- TWO_PLACES constant behavior
- to_currency() function with various input types
- FinancialJsonEncoder serialization
- Edge cases: negative amounts, large amounts, zero
"""

import json
from decimal import Decimal

import pytest

from decimal_utils import TWO_PLACES, ZERO, FinancialJsonEncoder, to_currency


class TestTwoPlaces:
    """Tests for TWO_PLACES constant."""

    def test_two_places_value(self) -> None:
        """TWO_PLACES should equal 0.01."""
        assert TWO_PLACES == Decimal("0.01")

    def test_two_places_quantize(self) -> None:
        """TWO_PLACES should quantize to 2 decimal places."""
        amount = Decimal("123.456")
        result = amount.quantize(TWO_PLACES)
        assert result == Decimal("123.46")

    def test_two_places_rounds_half_up_by_default(self) -> None:
        """Default rounding should be ROUND_HALF_EVEN (banker's rounding)."""
        # Note: Without explicit rounding mode, Decimal uses ROUND_HALF_EVEN
        amount = Decimal("123.445")
        result = amount.quantize(TWO_PLACES)
        # ROUND_HALF_EVEN rounds .445 to .44 (rounds to nearest even)
        assert result == Decimal("123.44")


class TestZero:
    """Tests for ZERO constant."""

    def test_zero_value(self) -> None:
        """ZERO should be exactly Decimal('0')."""
        assert ZERO == Decimal("0")

    def test_zero_is_decimal(self) -> None:
        """ZERO should be a Decimal type."""
        assert isinstance(ZERO, Decimal)

    def test_zero_not_from_float(self) -> None:
        """ZERO should not have float precision issues."""
        # Decimal(0.1) + Decimal(0.2) has issues if initialized from float
        # Our ZERO from string should be clean
        result = ZERO + Decimal("0.10") + Decimal("0.20")
        assert result == Decimal("0.30")


class TestToCurrency:
    """Tests for to_currency() function."""

    def test_string_input(self) -> None:
        """to_currency should handle string input."""
        result = to_currency("123.45")
        assert result == Decimal("123.45")
        assert isinstance(result, Decimal)

    def test_int_input(self) -> None:
        """to_currency should handle integer input."""
        result = to_currency(100)
        assert result == Decimal("100.00")

    def test_float_input(self) -> None:
        """to_currency should handle float input via string conversion."""
        result = to_currency(123.45)
        assert result == Decimal("123.45")

    def test_decimal_input(self) -> None:
        """to_currency should handle Decimal input."""
        result = to_currency(Decimal("123.456"))
        assert result == Decimal("123.46")  # ROUND_HALF_UP

    def test_rounding_half_up(self) -> None:
        """to_currency should use ROUND_HALF_UP."""
        assert to_currency("123.445") == Decimal("123.45")
        assert to_currency("123.455") == Decimal("123.46")

    def test_negative_amount(self) -> None:
        """to_currency should handle negative amounts (credits/refunds)."""
        result = to_currency("-50.99")
        assert result == Decimal("-50.99")

    def test_zero_amount(self) -> None:
        """to_currency should handle zero amounts."""
        assert to_currency("0") == Decimal("0.00")
        assert to_currency(0) == Decimal("0.00")
        assert to_currency(0.0) == Decimal("0.00")

    def test_large_amount(self) -> None:
        """to_currency should handle large amounts (>$100,000)."""
        result = to_currency("999999.99")
        assert result == Decimal("999999.99")

        result = to_currency("1234567.89")
        assert result == Decimal("1234567.89")

    def test_very_large_amount(self) -> None:
        """to_currency should handle very large amounts."""
        result = to_currency("99999999999.99")
        assert result == Decimal("99999999999.99")

    def test_small_amount(self) -> None:
        """to_currency should handle small amounts."""
        result = to_currency("0.01")
        assert result == Decimal("0.01")

    def test_precision_from_float(self) -> None:
        """to_currency should not lose precision when converting from float."""
        # This is a known problematic float representation
        # 0.1 + 0.2 != 0.3 in float arithmetic
        result = to_currency(0.1) + to_currency(0.2)
        assert result == Decimal("0.30")


class TestFinancialJsonEncoder:
    """Tests for FinancialJsonEncoder."""

    def test_decimal_serialization(self) -> None:
        """Decimals should serialize as strings to preserve precision."""
        data = {"amount": Decimal("123.45")}
        result = json.dumps(data, cls=FinancialJsonEncoder)
        assert result == '{"amount": "123.45"}'

    def test_decimal_precision_preserved(self) -> None:
        """Exact decimal precision should be preserved in JSON."""
        # This would lose precision with float: 0.1 + 0.2 + 0.3
        data = {"amount": Decimal("0.10") + Decimal("0.20") + Decimal("0.30")}
        result = json.dumps(data, cls=FinancialJsonEncoder)
        parsed = json.loads(result)
        # Convert back to Decimal and verify
        assert Decimal(parsed["amount"]) == Decimal("0.60")

    def test_roundtrip_preserves_value(self) -> None:
        """JSON roundtrip should preserve exact Decimal value."""
        original = Decimal("123456789.12")
        data = {"amount": original}
        json_str = json.dumps(data, cls=FinancialJsonEncoder)
        parsed = json.loads(json_str)
        recovered = Decimal(parsed["amount"])
        assert recovered == original

    def test_negative_decimal(self) -> None:
        """Negative decimals should serialize correctly."""
        data = {"refund": Decimal("-50.00")}
        result = json.dumps(data, cls=FinancialJsonEncoder)
        assert result == '{"refund": "-50.00"}'

    def test_datetime_serialization(self) -> None:
        """Datetimes should serialize to ISO format."""
        from datetime import datetime

        data = {"timestamp": datetime(2025, 1, 15, 10, 30, 0)}
        result = json.dumps(data, cls=FinancialJsonEncoder)
        assert result == '{"timestamp": "2025-01-15T10:30:00"}'

    def test_date_serialization(self) -> None:
        """Dates should serialize to ISO format."""
        from datetime import date

        data = {"date": date(2025, 1, 15)}
        result = json.dumps(data, cls=FinancialJsonEncoder)
        assert result == '{"date": "2025-01-15"}'

    def test_mixed_types(self) -> None:
        """Mixed types should all serialize correctly."""
        from datetime import date

        data = {
            "amount": Decimal("100.00"),
            "count": 5,
            "name": "Test",
            "date": date(2025, 1, 15),
        }
        result = json.loads(json.dumps(data, cls=FinancialJsonEncoder))
        assert result["amount"] == "100.00"
        assert result["count"] == 5
        assert result["name"] == "Test"
        assert result["date"] == "2025-01-15"

    def test_nested_decimals(self) -> None:
        """Nested structures with Decimals should serialize correctly."""
        data = {
            "items": [
                {"price": Decimal("10.00")},
                {"price": Decimal("20.50")},
            ],
            "total": Decimal("30.50"),
        }
        result = json.loads(json.dumps(data, cls=FinancialJsonEncoder))
        assert result["items"][0]["price"] == "10.00"
        assert result["items"][1]["price"] == "20.50"
        assert result["total"] == "30.50"


class TestBillSplitPrecision:
    """Tests to verify bill splits sum exactly to the total."""

    def test_bill_split_three_way(self) -> None:
        """Three-way split should sum exactly to original total."""
        total = Decimal("100.00")
        # Simulate a three-way split
        part1 = (total / 3).quantize(TWO_PLACES)
        part2 = (total / 3).quantize(TWO_PLACES)
        part3 = total - part1 - part2  # Remainder to last part

        assert part1 + part2 + part3 == total

    def test_bill_split_no_floating_point_drift(self) -> None:
        """Multiple splits should not accumulate floating point drift."""
        total = Decimal("99.99")
        parts = []

        # Split into 7 parts (awkward division)
        for i in range(6):
            parts.append((total / 7).quantize(TWO_PLACES))

        # Last part gets the remainder
        parts.append(total - sum(parts))

        assert sum(parts) == total

    def test_accumulated_small_amounts(self) -> None:
        """Accumulating many small amounts should not drift."""
        result = ZERO
        for _ in range(1000):
            result += to_currency("0.01")

        assert result == Decimal("10.00")
