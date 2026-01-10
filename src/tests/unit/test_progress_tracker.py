"""Tests for progress_tracker.py exception handling."""

import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError


class TestDailySalesProgressTrackerExceptionHandling(unittest.TestCase):
    """Test that ClientError exceptions are properly caught and handled."""

    def _create_client_error(self, code: str = "ValidationException") -> ClientError:
        """Helper to create a ClientError for testing."""
        return ClientError(
            error_response={"Error": {"Code": code, "Message": "Test error"}},
            operation_name="TestOperation",
        )

    @patch.dict("os.environ", {"DAILY_SALES_PROGRESS_TABLE": "test-table"})
    @patch("progress_tracker.dynamodb")
    def test_initialize_progress_handles_client_error(
        self, mock_dynamodb: MagicMock
    ) -> None:
        """Test that initialize_progress catches ClientError and doesn't raise."""
        from progress_tracker import DailySalesProgressTracker

        # Set up mock table that raises ClientError on put_item
        mock_table = MagicMock()
        mock_table.put_item.side_effect = self._create_client_error()
        mock_dynamodb.Table.return_value = mock_table

        tracker = DailySalesProgressTracker()

        # This should NOT raise - it should catch the ClientError and log it
        tracker.initialize_progress(
            request_id="test-request-123",
            stores=["20400", "20407"],
            txdate=date(2024, 1, 15),
        )

        # Verify put_item was called
        mock_table.put_item.assert_called_once()

    @patch.dict("os.environ", {"DAILY_SALES_PROGRESS_TABLE": "test-table"})
    @patch("progress_tracker.dynamodb")
    def test_update_store_completion_handles_client_error(
        self, mock_dynamodb: MagicMock
    ) -> None:
        """Test that update_store_completion catches ClientError and returns default dict."""
        from progress_tracker import DailySalesProgressTracker

        # Set up mock table that raises ClientError on update_item
        mock_table = MagicMock()
        mock_table.update_item.side_effect = self._create_client_error()
        mock_dynamodb.Table.return_value = mock_table

        tracker = DailySalesProgressTracker()

        # This should NOT raise - it should catch the ClientError and return default
        result = tracker.update_store_completion(
            request_id="test-request-123",
            store="20400",
            status="completed",
        )

        # Verify we get the default error response
        self.assertEqual(result["completed"], 0)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["total"], 0)
        self.assertFalse(result["is_complete"])
        self.assertEqual(result["store_statuses"], {})

    @patch.dict("os.environ", {"DAILY_SALES_PROGRESS_TABLE": "test-table"})
    @patch("progress_tracker.dynamodb")
    def test_update_store_completion_success(self, mock_dynamodb: MagicMock) -> None:
        """Test that update_store_completion works correctly on success."""
        from progress_tracker import DailySalesProgressTracker

        # Set up mock table with successful response
        mock_table = MagicMock()
        mock_table.update_item.return_value = {
            "Attributes": {
                "total_stores": 2,
                "completed_stores": 1,
                "failed_stores": 0,
                "store_statuses": {"20400": "completed", "20407": "dispatched"},
            }
        }
        mock_dynamodb.Table.return_value = mock_table

        tracker = DailySalesProgressTracker()

        result = tracker.update_store_completion(
            request_id="test-request-123",
            store="20400",
            status="completed",
        )

        # Verify successful response
        self.assertEqual(result["completed"], 1)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["total"], 2)
        self.assertFalse(result["is_complete"])

    def test_no_table_configured(self) -> None:
        """Test graceful handling when no table is configured."""
        from progress_tracker import DailySalesProgressTracker

        with patch.dict("os.environ", {}, clear=True):
            # Remove the env var if it exists
            import os

            os.environ.pop("DAILY_SALES_PROGRESS_TABLE", None)

            tracker = DailySalesProgressTracker()

            # Should not raise, just log warning
            tracker.initialize_progress(
                request_id="test-request-123",
                stores=["20400"],
                txdate=date(2024, 1, 15),
            )

            # Should return default dict
            result = tracker.update_store_completion(
                request_id="test-request-123",
                store="20400",
                status="completed",
            )
            self.assertEqual(result["completed"], 0)
            self.assertFalse(result["is_complete"])


if __name__ == "__main__":
    unittest.main()
