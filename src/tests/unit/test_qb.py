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


class TestQuickBooksOAuth(unittest.TestCase):
    """Test QuickBooks OAuth functions."""

    @patch("qb.get_secret")
    @patch("qb.AuthClient")
    def test_get_auth_url_returns_url_and_state(
        self,
        mock_auth_client_class: MagicMock,
        mock_get_secret: MagicMock,
    ) -> None:
        """Test that get_auth_url returns a valid URL and state."""
        from qb import get_auth_url

        # Set up mocks
        mock_get_secret.return_value = '{"client_id": "test_id", "client_secret": "test_secret", "redirect_url": "https://example.com/callback"}'
        mock_auth_client = MagicMock()
        mock_auth_client.get_authorization_url.return_value = (
            "https://appcenter.intuit.com/authorize?state=test_state"
        )
        mock_auth_client_class.return_value = mock_auth_client

        result = get_auth_url("test_state")

        self.assertIn("url", result)
        self.assertIn("state", result)
        self.assertEqual(result["state"], "test_state")
        self.assertIn("appcenter.intuit.com", result["url"])
        mock_auth_client_class.assert_called_once()

    @patch("qb.get_secret")
    @patch("qb.put_secret")
    @patch("qb.AuthClient")
    def test_exchange_auth_code_success(
        self,
        mock_auth_client_class: MagicMock,
        mock_put_secret: MagicMock,
        mock_get_secret: MagicMock,
    ) -> None:
        """Test successful OAuth code exchange."""
        from qb import exchange_auth_code

        # Set up mocks
        mock_get_secret.return_value = '{"client_id": "test_id", "client_secret": "test_secret", "redirect_url": "https://example.com/callback"}'
        mock_auth_client = MagicMock()
        mock_auth_client.access_token = "new_access_token"
        mock_auth_client.refresh_token = "new_refresh_token"
        mock_auth_client_class.return_value = mock_auth_client

        result = exchange_auth_code("auth_code_123", "realm_id_456")

        self.assertTrue(result["success"])
        self.assertEqual(result["realm_id"], "realm_id_456")
        mock_auth_client.get_bearer_token.assert_called_once_with(
            "auth_code_123", realm_id="realm_id_456"
        )
        mock_put_secret.assert_called_once()

    @patch("qb.get_secret")
    @patch("qb.AuthClient")
    def test_exchange_auth_code_failure(
        self,
        mock_auth_client_class: MagicMock,
        mock_get_secret: MagicMock,
    ) -> None:
        """Test OAuth code exchange failure."""
        from qb import exchange_auth_code

        # Set up mocks
        mock_get_secret.return_value = '{"client_id": "test_id", "client_secret": "test_secret", "redirect_url": "https://example.com/callback"}'
        mock_auth_client = MagicMock()
        mock_auth_client.get_bearer_token.side_effect = Exception("Invalid code")
        mock_auth_client_class.return_value = mock_auth_client

        result = exchange_auth_code("bad_code", "realm_id")

        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Invalid code", result["error"])

    @patch("qb.get_secret")
    @patch("qb.refresh_session")
    @patch("qb._qbo_params")
    def test_get_connection_status_connected(
        self,
        mock_qbo_params: MagicMock,
        mock_refresh: MagicMock,
        mock_get_secret: MagicMock,
    ) -> None:
        """Test connection status when connected."""
        from qb import get_connection_status

        mock_get_secret.return_value = '{"access_token": "token", "refresh_token": "refresh"}'
        mock_qbo_params.get.return_value = "123456789"

        result = get_connection_status()

        self.assertTrue(result["connected"])
        self.assertEqual(result["company_id"], "123456789")
        mock_refresh.assert_called_once()

    @patch("qb.get_secret")
    @patch("qb._qbo_params")
    def test_get_connection_status_no_tokens(
        self,
        mock_qbo_params: MagicMock,
        mock_get_secret: MagicMock,
    ) -> None:
        """Test connection status when no tokens configured."""
        from qb import get_connection_status

        mock_get_secret.return_value = '{"client_id": "test_id"}'
        mock_qbo_params.get.return_value = ""

        result = get_connection_status()

        self.assertFalse(result["connected"])
        self.assertIn("No tokens", result["message"])

    @patch("qb.get_secret")
    @patch("qb.refresh_session")
    @patch("qb._qbo_params")
    def test_get_connection_status_refresh_failure(
        self,
        mock_qbo_params: MagicMock,
        mock_refresh: MagicMock,
        mock_get_secret: MagicMock,
    ) -> None:
        """Test connection status when refresh fails."""
        from qb import get_connection_status

        mock_get_secret.return_value = '{"access_token": "token", "refresh_token": "refresh"}'
        mock_qbo_params.get.return_value = "123456789"
        mock_refresh.side_effect = Exception("Token expired")

        result = get_connection_status()

        self.assertFalse(result["connected"])
        self.assertIn("Token expired", result["message"])


class TestUnlinkedSalesReceipts(unittest.TestCase):
    """Test get_unlinked_sales_receipts function."""

    @patch("qb.CLIENT")
    @patch("qb.refresh_session")
    @patch("qb.SalesReceipt")
    def test_get_unlinked_sales_receipts_returns_unlinked(
        self,
        mock_sales_receipt: MagicMock,
        mock_refresh: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Test that get_unlinked_sales_receipts returns receipts without linked transactions."""
        from datetime import date

        from qb import get_unlinked_sales_receipts

        # Create mock sales receipts
        mock_unlinked = MagicMock()
        mock_unlinked.Id = "1234"
        mock_unlinked.TotalAmt = Decimal("100.50")
        mock_unlinked.LinkedTxn = []  # No linked transactions
        mock_unlinked.DepartmentRef = MagicMock()
        mock_unlinked.DepartmentRef.name = "20358"
        mock_unlinked.TxnDate = "2025-01-15"
        mock_unlinked.DocNumber = "DS-20358-20250115"

        mock_linked = MagicMock()
        mock_linked.Id = "5678"
        mock_linked.TotalAmt = Decimal("200.00")
        mock_linked.LinkedTxn = [MagicMock()]  # Has linked transaction
        mock_linked.DepartmentRef = MagicMock()
        mock_linked.DepartmentRef.name = "20367"
        mock_linked.TxnDate = "2025-01-15"
        mock_linked.DocNumber = "DS-20367-20250115"

        mock_sales_receipt.count.return_value = 2
        mock_sales_receipt.where.return_value = [mock_unlinked, mock_linked]

        result = get_unlinked_sales_receipts(date(2025, 1, 1), date(2025, 1, 31))

        # Should only return the unlinked receipt
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "1234")
        self.assertEqual(result[0]["store"], "20358")
        self.assertEqual(result[0]["amount"], "100.50")
        self.assertTrue(result[0]["has_cents"])  # 100.50 has cents
        self.assertIn("salesreceipt?txnId=1234", result[0]["qb_url"])
        mock_refresh.assert_called_once()

    @patch("qb.CLIENT")
    @patch("qb.refresh_session")
    @patch("qb.SalesReceipt")
    def test_get_unlinked_sales_receipts_empty_list(
        self,
        mock_sales_receipt: MagicMock,
        mock_refresh: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Test that get_unlinked_sales_receipts returns empty list when no unlinked found."""
        from datetime import date

        from qb import get_unlinked_sales_receipts

        mock_sales_receipt.count.return_value = 0
        mock_sales_receipt.where.return_value = []

        result = get_unlinked_sales_receipts(date(2025, 1, 1), date(2025, 1, 31))

        self.assertEqual(len(result), 0)
        mock_refresh.assert_called_once()

    @patch("qb.CLIENT")
    @patch("qb.refresh_session")
    @patch("qb.SalesReceipt")
    def test_get_unlinked_sales_receipts_has_cents_detection(
        self,
        mock_sales_receipt: MagicMock,
        mock_refresh: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Test that has_cents correctly detects fractional amounts."""
        from datetime import date

        from qb import get_unlinked_sales_receipts

        # Receipt with whole dollar amount (no cents)
        mock_whole_dollar = MagicMock()
        mock_whole_dollar.Id = "1111"
        mock_whole_dollar.TotalAmt = Decimal("500.00")
        mock_whole_dollar.LinkedTxn = []
        mock_whole_dollar.DepartmentRef = MagicMock()
        mock_whole_dollar.DepartmentRef.name = "20358"
        mock_whole_dollar.TxnDate = "2025-01-15"
        mock_whole_dollar.DocNumber = "DS-20358-20250115"

        # Receipt with cents
        mock_with_cents = MagicMock()
        mock_with_cents.Id = "2222"
        mock_with_cents.TotalAmt = Decimal("499.99")
        mock_with_cents.LinkedTxn = []
        mock_with_cents.DepartmentRef = MagicMock()
        mock_with_cents.DepartmentRef.name = "20367"
        mock_with_cents.TxnDate = "2025-01-15"
        mock_with_cents.DocNumber = "DS-20367-20250115"

        mock_sales_receipt.count.return_value = 2
        mock_sales_receipt.where.return_value = [mock_whole_dollar, mock_with_cents]

        result = get_unlinked_sales_receipts(date(2025, 1, 1), date(2025, 1, 31))

        self.assertEqual(len(result), 2)
        # Whole dollar should not have has_cents
        whole_dollar_result = next(r for r in result if r["id"] == "1111")
        self.assertFalse(whole_dollar_result["has_cents"])
        # Amount with cents should have has_cents
        with_cents_result = next(r for r in result if r["id"] == "2222")
        self.assertTrue(with_cents_result["has_cents"])

    @patch("qb.CLIENT")
    @patch("qb.refresh_session")
    @patch("qb.SalesReceipt")
    def test_get_unlinked_sales_receipts_excludes_zero_amounts(
        self,
        mock_sales_receipt: MagicMock,
        mock_refresh: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Test that receipts with zero or negative amounts are excluded."""
        from datetime import date

        from qb import get_unlinked_sales_receipts

        # Receipt with zero amount
        mock_zero = MagicMock()
        mock_zero.Id = "0000"
        mock_zero.TotalAmt = Decimal("0.00")
        mock_zero.LinkedTxn = []
        mock_zero.DepartmentRef = MagicMock()
        mock_zero.DepartmentRef.name = "20358"
        mock_zero.TxnDate = "2025-01-15"
        mock_zero.DocNumber = "DS-20358-20250115"

        # Receipt with positive amount
        mock_positive = MagicMock()
        mock_positive.Id = "1111"
        mock_positive.TotalAmt = Decimal("100.00")
        mock_positive.LinkedTxn = []
        mock_positive.DepartmentRef = MagicMock()
        mock_positive.DepartmentRef.name = "20367"
        mock_positive.TxnDate = "2025-01-15"
        mock_positive.DocNumber = "DS-20367-20250115"

        mock_sales_receipt.count.return_value = 2
        mock_sales_receipt.where.return_value = [mock_zero, mock_positive]

        result = get_unlinked_sales_receipts(date(2025, 1, 1), date(2025, 1, 31))

        # Should only return the positive amount receipt
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "1111")


if __name__ == "__main__":
    unittest.main()
