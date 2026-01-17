"""Tests for the timeout_detector_handler in lambda_function.py"""

import json
import time
import unittest
from unittest.mock import MagicMock, patch


class TestTimeoutDetectorHandler(unittest.TestCase):
    """Test timeout_detector_handler function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Set required environment variables
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "TASK_STATES_TABLE": "test-task-states",
                "CONNECTIONS_TABLE": "test-connections",
                "WEBSOCKET_ENDPOINT": "https://test.execute-api.us-east-2.amazonaws.com/prod",
                "OPERATION_TIMEOUTS": json.dumps(
                    {
                        "daily_sales": 600,
                        "invoice_sync": 660,
                        "email_tips": 540,
                    }
                ),
            },
        )
        self.env_patcher.start()

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.env_patcher.stop()

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_marks_stale_task_as_failed(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that stale tasks are marked as failed."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Simulate a stale task (updated 10 minutes ago, timeout is 600s)
        stale_time = int(time.time()) - 700  # 700 seconds ago

        def mock_query(**kwargs: dict) -> dict:
            """Return stale task only for daily_sales operation."""
            expr_values = kwargs.get("ExpressionAttributeValues", {})
            if expr_values.get(":op") == "daily_sales":
                return {
                    "Items": [
                        {
                            "task_id": "stale-task-123",
                            "timestamp": stale_time,
                            "operation": "daily_sales",
                            "status": "started",
                            "updated_at": stale_time,
                            "created_at": stale_time,
                        }
                    ]
                }
            return {"Items": []}

        mock_table.query.side_effect = mock_query

        result = timeout_detector_handler({}, None)

        # Verify task was marked as failed
        self.assertEqual(result["marked_failed"], 1)

        # Verify put_item was called with failed status
        put_calls = mock_table.put_item.call_args_list
        self.assertTrue(
            any(call[1]["Item"]["status"] == "failed" for call in put_calls)
        )

        # Verify WebSocket broadcast was called
        mock_ws.broadcast_status.assert_called()
        call_args = mock_ws.broadcast_status.call_args
        self.assertEqual(call_args[1]["status"], "failed")
        self.assertIn("timed out", call_args[1]["error"])

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_does_not_mark_recent_task(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that recent tasks are not marked as failed."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Simulate a recent task (updated 1 minute ago, timeout is 600s)
        recent_time = int(time.time()) - 60  # 60 seconds ago
        mock_table.query.return_value = {
            "Items": [
                {
                    "task_id": "recent-task-123",
                    "timestamp": recent_time,
                    "operation": "daily_sales",
                    "status": "processing",
                    "updated_at": recent_time,
                    "created_at": recent_time,
                }
            ]
        }

        result = timeout_detector_handler({}, None)

        # Verify no tasks were marked as failed
        self.assertEqual(result["marked_failed"], 0)

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_handles_empty_results(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that handler handles no tasks gracefully."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.query.return_value = {"Items": []}

        result = timeout_detector_handler({}, None)

        self.assertEqual(result["marked_failed"], 0)

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_deduplicates_tasks_by_id(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that multiple records for same task_id are deduplicated."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Simulate multiple records for same task (older one is stale, newer is recent)
        stale_time = int(time.time()) - 700
        recent_time = int(time.time()) - 60
        mock_table.query.return_value = {
            "Items": [
                {
                    "task_id": "task-123",
                    "timestamp": stale_time,
                    "operation": "daily_sales",
                    "status": "started",
                    "updated_at": stale_time,
                    "created_at": stale_time,
                },
                {
                    "task_id": "task-123",
                    "timestamp": recent_time,
                    "operation": "daily_sales",
                    "status": "processing",
                    "updated_at": recent_time,
                    "created_at": stale_time,
                },
            ]
        }

        result = timeout_detector_handler({}, None)

        # Should use the most recent record, which is not stale
        self.assertEqual(result["marked_failed"], 0)

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_uses_default_timeout_for_unknown_operation(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that default timeout (600s) is used for operations not in config."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # daily_journal is not in our test OPERATION_TIMEOUTS
        stale_time = int(time.time()) - 700  # 700s ago, exceeds default 600s

        def mock_query(**kwargs: dict) -> dict:
            """Return stale task only for daily_journal operation."""
            expr_values = kwargs.get("ExpressionAttributeValues", {})
            if expr_values.get(":op") == "daily_journal":
                return {
                    "Items": [
                        {
                            "task_id": "task-456",
                            "timestamp": stale_time,
                            "operation": "daily_journal",
                            "status": "started",
                            "updated_at": stale_time,
                            "created_at": stale_time,
                        }
                    ]
                }
            return {"Items": []}

        mock_table.query.side_effect = mock_query

        result = timeout_detector_handler({}, None)

        # Should be marked as failed using default 600s timeout
        self.assertEqual(result["marked_failed"], 1)

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_handles_query_exception(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that handler continues processing after query exceptions."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.query.side_effect = Exception("DynamoDB error")

        # Should not raise, should return 0 marked
        result = timeout_detector_handler({}, None)

        self.assertEqual(result["marked_failed"], 0)

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_handles_invalid_operation_timeouts_json(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that handler handles invalid OPERATION_TIMEOUTS JSON."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.query.return_value = {"Items": []}

        # Override with invalid JSON
        with patch.dict("os.environ", {"OPERATION_TIMEOUTS": "invalid-json"}):
            result = timeout_detector_handler({}, None)

        # Should still complete without error
        self.assertEqual(result["marked_failed"], 0)


if __name__ == "__main__":
    unittest.main()
