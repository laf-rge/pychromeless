import unittest
from decimal import Decimal
from ..qb import calculate_bill_splits


class TestQuickBooks(unittest.TestCase):
    def test_equal_bill_split(self):
        """Test splitting a bill equally between 5 locations."""
        # Test case: $256.36 split over 5 locations
        total = Decimal("256.36")
        line_amounts = [Decimal("256.36")]
        locations = ["20025", "20358", "20366", "20367", "20368"]

        splits = calculate_bill_splits(total, line_amounts, locations)

        # Verify total matches exactly
        total_split = sum(sum(amounts) for amounts in splits.values())
        self.assertEqual(total, total_split)

        # Verify each location gets close to expected share
        expected_share = total / len(locations)  # $51.272
        for loc, amounts in splits.items():
            loc_total = sum(amounts)
            # Check that each location is within a penny of expected
            self.assertLess(abs(loc_total - expected_share), Decimal("0.01"))
            # Check that amounts have exactly 2 decimal places
            for amount in amounts:
                self.assertEqual(amount.as_tuple().exponent, -2)

        # Verify specific amounts
        self.assertEqual(splits["20025"][0], Decimal("51.27"))
        self.assertEqual(splits["20358"][0], Decimal("51.27"))
        self.assertEqual(splits["20366"][0], Decimal("51.27"))
        self.assertEqual(splits["20367"][0], Decimal("51.27"))
        self.assertEqual(
            splits["20368"][0], Decimal("51.28")
        )  # Last location gets extra penny

    def test_custom_ratio_split(self):
        """Test splitting a bill with custom ratios."""
        total = Decimal("100.00")
        line_amounts = [Decimal("100.00")]
        locations = ["20025", "20358", "20366"]
        split_ratios = {
            "20025": Decimal("0.5"),  # 50%
            "20358": Decimal("0.3"),  # 30%
            "20366": Decimal("0.2"),  # 20%
        }

        splits = calculate_bill_splits(total, line_amounts, locations, split_ratios)

        # Verify total matches
        total_split = sum(sum(amounts) for amounts in splits.values())
        self.assertEqual(total, total_split)

        # Verify expected amounts
        self.assertEqual(splits["20025"][0], Decimal("50.00"))
        self.assertEqual(splits["20358"][0], Decimal("30.00"))
        self.assertEqual(splits["20366"][0], Decimal("20.00"))

    def test_multiple_line_items(self):
        """Test splitting a bill with multiple line items."""
        total = Decimal("150.00")
        line_amounts = [Decimal("100.00"), Decimal("50.00")]
        locations = ["20025", "20358", "20366"]

        splits = calculate_bill_splits(total, line_amounts, locations)

        # Verify total matches
        total_split = sum(sum(amounts) for amounts in splits.values())
        self.assertEqual(total, total_split)

        # Each location should have two line items
        for amounts in splits.values():
            self.assertEqual(len(amounts), 2)

        # Verify line items sum correctly for each location
        for amounts in splits.values():
            self.assertLess(abs(sum(amounts) - Decimal("50.00")), Decimal("0.01"))

    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        total = Decimal("100.00")
        line_amounts = [Decimal("100.00")]

        # Test empty locations list
        with self.assertRaises(ValueError):
            calculate_bill_splits(total, line_amounts, [])

        # Test invalid split ratios
        locations = ["20025", "20358"]
        bad_ratios = {
            "20025": Decimal("0.6"),
            "20358": Decimal("0.6"),  # Sums to 1.2
        }
        with self.assertRaises(ValueError):
            calculate_bill_splits(total, line_amounts, locations, bad_ratios)


if __name__ == "__main__":
    unittest.main()
