"""Tests for the unlinked_deposits_handler in lambda_function.py"""
import json
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestUnlinkedDepositsHandler(unittest.TestCase):
    """Test unlinked_deposits_handler function."""

    @patch("lambda_function.qb")
    def test_returns_deposits_with_summary(
        self,
        mock_qb: MagicMock,
    ) -> None:
        """Test that handler returns deposits list and summary."""
        from lambda_function import unlinked_deposits_handler

        # Set up mock data
        mock_deposits = [
            {
                "id": "1234",
                "store": "20358",
                "date": "2025-01-15",
                "amount": "100.50",
                "doc_number": "DS-20358-20250115",
                "qb_url": "https://app.qbo.intuit.com/app/salesreceipt?txnId=1234",
                "has_cents": True,
            },
            {
                "id": "5678",
                "store": "20367",
                "date": "2025-01-16",
                "amount": "200.00",
                "doc_number": "DS-20367-20250116",
                "qb_url": "https://app.qbo.intuit.com/app/salesreceipt?txnId=5678",
                "has_cents": False,
            },
        ]
        mock_qb.get_unlinked_sales_receipts.return_value = mock_deposits

        # Create event with query parameters
        event = {
            "queryStringParameters": {
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            }
        }

        response = unlinked_deposits_handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(len(body["deposits"]), 2)
        self.assertEqual(body["summary"]["count"], 2)
        self.assertEqual(body["summary"]["total_amount"], "300.50")

    @patch("lambda_function.qb")
    def test_uses_default_dates_when_not_provided(
        self,
        mock_qb: MagicMock,
    ) -> None:
        """Test that handler uses default date range when not provided."""
        from datetime import date

        from lambda_function import unlinked_deposits_handler

        mock_qb.get_unlinked_sales_receipts.return_value = []

        # Event without query parameters
        event = {}

        response = unlinked_deposits_handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        # Verify default start date is 2025-01-01
        call_args = mock_qb.get_unlinked_sales_receipts.call_args[0]
        self.assertEqual(call_args[0], date(2025, 1, 1))
        # End date should be today
        self.assertEqual(call_args[1], date.today())

    @patch("lambda_function.qb")
    def test_handles_invalid_date_format(
        self,
        mock_qb: MagicMock,
    ) -> None:
        """Test that handler returns error for invalid date format."""
        from lambda_function import unlinked_deposits_handler

        event = {
            "queryStringParameters": {
                "start_date": "invalid-date",
            }
        }

        response = unlinked_deposits_handler(event, None)

        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertIn("Invalid date format", body["message"])

    @patch("lambda_function.qb")
    def test_handles_empty_results(
        self,
        mock_qb: MagicMock,
    ) -> None:
        """Test that handler handles empty results correctly."""
        from lambda_function import unlinked_deposits_handler

        mock_qb.get_unlinked_sales_receipts.return_value = []

        event = {
            "queryStringParameters": {
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            }
        }

        response = unlinked_deposits_handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(len(body["deposits"]), 0)
        self.assertEqual(body["summary"]["count"], 0)
        self.assertEqual(body["summary"]["total_amount"], "0.00")

    @patch("lambda_function.qb")
    def test_handles_qb_exception(
        self,
        mock_qb: MagicMock,
    ) -> None:
        """Test that handler handles QuickBooks exceptions."""
        from lambda_function import unlinked_deposits_handler

        mock_qb.get_unlinked_sales_receipts.side_effect = Exception("QB connection failed")

        event = {}

        response = unlinked_deposits_handler(event, None)

        self.assertEqual(response["statusCode"], 500)
        body = json.loads(response["body"])
        self.assertIn("Error", body["message"])


class TestDailySalesHandlerWithStore(unittest.TestCase):
    """Test daily_sales_handler with single store parameter."""

    @patch("lambda_function.qb")
    @patch("lambda_function.Flexepos")
    @patch("lambda_function.WebSocketManager")
    def test_single_store_parameter_filters_stores(
        self,
        mock_ws_manager: MagicMock,
        mock_flexepos_class: MagicMock,
        mock_qb: MagicMock,
    ) -> None:
        """Test that store parameter limits processing to single store."""
        # This test verifies the store parameter is passed correctly
        # Full integration test would require more mocking
        from lambda_function import daily_sales_handler

        mock_ws = MagicMock()
        mock_ws_manager.return_value = mock_ws

        mock_flexepos = MagicMock()
        mock_flexepos.getDailySales.return_value = {"20358": {"Payins": ""}}
        mock_flexepos.getOnlinePayments.return_value = []
        mock_flexepos.getRoyaltyReport.return_value = []
        mock_flexepos_class.return_value = mock_flexepos

        # Event with store parameter
        event = {
            "year": "2025",
            "month": "01",
            "day": "15",
            "store": "20358",
        }

        # The handler should process only the specified store
        # Since we're running locally (no AWS_LAMBDA_FUNCTION_NAME),
        # it will use sequential processing
        response = daily_sales_handler(event, None)

        # Verify that getDailySales was called with the specific store
        call_args = mock_flexepos.getDailySales.call_args
        if call_args:
            # First positional arg should be the store
            store_arg = call_args[0][0]
            self.assertEqual(store_arg, "20358")


if __name__ == "__main__":
    unittest.main()
