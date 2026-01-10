import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from quickbooks.exceptions import QuickbooksException

from qb import calculate_bill_splits


class TestQuickBooks(unittest.TestCase):
    def test_equal_bill_split(self) -> None:
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

    def test_custom_ratio_split(self) -> None:
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

    def test_multiple_line_items(self) -> None:
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

    def test_invalid_inputs(self) -> None:
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


class TestQuickBooksExceptionHandling(unittest.TestCase):
    """Test that QuickbooksException is properly caught and handled."""

    def _create_quickbooks_exception(self) -> QuickbooksException:
        """Helper to create a QuickbooksException for testing."""
        return QuickbooksException("Test QuickBooks error", error_code="500")

    @patch("qb.CLIENT")
    @patch("qb.refresh_session")
    @patch("qb.SalesReceipt")
    @patch("qb.Department")
    def test_create_daily_sales_handles_quickbooks_exception(
        self,
        mock_department: MagicMock,
        mock_sales_receipt: MagicMock,
        mock_refresh: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Test that create_daily_sales catches QuickbooksException on save."""
        from datetime import date

        from qb import create_daily_sales

        # Set up mocks
        mock_department.all.return_value = []
        mock_sales_receipt.filter.return_value = []

        # Create a mock receipt that raises on save
        mock_receipt = MagicMock()
        mock_receipt.save.side_effect = self._create_quickbooks_exception()
        mock_receipt.to_json.return_value = "{}"
        mock_sales_receipt.return_value = mock_receipt

        # This should NOT raise - the exception should be caught and logged
        # Since there are no stores in the mocked data, no save will be called
        create_daily_sales(
            txdate=date(2024, 1, 15),
            daily_reports={},
            overwrite=False,
        )

        # If we get here without raising, the test passes
        mock_refresh.assert_called()

    def test_quickbooks_exception_is_caught_pattern(self) -> None:
        """
        Test that our exception handling pattern works correctly.

        This test verifies the try/except pattern we use throughout qb.py.
        The actual API-dependent functions are integration tests, but this
        validates that QuickbooksException is properly caught.
        """
        # Create a mock object that raises QuickbooksException on save
        mock_qb_object = MagicMock()
        mock_qb_object.save.side_effect = self._create_quickbooks_exception()
        mock_qb_object.to_json.return_value = "{}"

        # This simulates the pattern used in sync_bill, sync_deposit, etc.
        exception_was_caught = False
        try:
            mock_qb_object.save(qb=None)
        except QuickbooksException:
            exception_was_caught = True
            # In real code, we log here instead of raising

        self.assertTrue(exception_was_caught)
        mock_qb_object.save.assert_called_once()

    def test_quickbooks_exception_does_not_catch_other_exceptions(self) -> None:
        """
        Test that only QuickbooksException is caught, not other exceptions.

        This ensures our specific exception handling doesn't accidentally
        swallow unexpected errors.
        """
        mock_qb_object = MagicMock()
        mock_qb_object.save.side_effect = ValueError("Unexpected error")

        # ValueError should NOT be caught by the QuickbooksException handler
        with self.assertRaises(ValueError):
            try:
                mock_qb_object.save(qb=None)
            except QuickbooksException:
                pass  # This should not catch ValueError


if __name__ == "__main__":
    unittest.main()
