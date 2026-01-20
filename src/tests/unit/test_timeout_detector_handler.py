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
            """Return stale task for both GSI query and direct query."""
            # GSI query for started/processing tasks
            if kwargs.get("IndexName") == "operation_type-index":
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
            # Direct query for latest status - return same stale record
            else:
                return {
                    "Items": [
                        {
                            "task_id": "stale-task-123",
                            "timestamp": stale_time,
                            "operation": "daily_sales",
                            "status": "started",
                            "updated_at": stale_time,
                        }
                    ]
                }

        mock_table.query.side_effect = mock_query

        result = timeout_detector_handler({}, None)

        # Verify task was marked as failed
        self.assertEqual(result["marked_failed"], 1)

        # Verify update_item was called with failed status
        update_calls = mock_table.update_item.call_args_list
        self.assertEqual(len(update_calls), 1)
        call_kwargs = update_calls[0][1]
        self.assertEqual(call_kwargs["Key"]["task_id"], "stale-task-123")
        self.assertIn(":status", call_kwargs["ExpressionAttributeValues"])
        self.assertEqual(call_kwargs["ExpressionAttributeValues"][":status"], "failed")

        # Verify WebSocket broadcast_only was called (not broadcast_status)
        mock_ws.broadcast_only.assert_called()
        call_args = mock_ws.broadcast_only.call_args
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

        def mock_query(**kwargs: dict) -> dict:
            """Return recent task for both GSI and direct query."""
            if kwargs.get("IndexName") == "operation_type-index":
                expr_values = kwargs.get("ExpressionAttributeValues", {})
                if expr_values.get(":op") == "daily_sales":
                    return {
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
                return {"Items": []}
            else:
                return {
                    "Items": [
                        {
                            "task_id": "recent-task-123",
                            "timestamp": recent_time,
                            "operation": "daily_sales",
                            "status": "processing",
                            "updated_at": recent_time,
                        }
                    ]
                }

        mock_table.query.side_effect = mock_query

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

        def mock_query(**kwargs: dict) -> dict:
            """Return empty results for all queries."""
            return {"Items": []}

        mock_table.query.side_effect = mock_query

        result = timeout_detector_handler({}, None)

        self.assertEqual(result["marked_failed"], 0)

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_recent_activity_prevents_timeout(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that recent activity prevents task from being marked as timed out."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Simulate multiple records: older one is stale, newer has recent activity
        stale_time = int(time.time()) - 700
        recent_time = int(time.time()) - 60

        def mock_query(**kwargs: dict) -> dict:
            """Return both records via GSI, and latest processing record via direct."""
            # GSI query for started/processing tasks
            if kwargs.get("IndexName") == "operation_type-index":
                expr_values = kwargs.get("ExpressionAttributeValues", {})
                if expr_values.get(":op") == "daily_sales":
                    return {
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
                return {"Items": []}
            # Direct query for latest status - return most recent processing record
            else:
                return {
                    "Items": [
                        {
                            "task_id": "task-123",
                            "timestamp": recent_time,
                            "operation": "daily_sales",
                            "status": "processing",
                            "updated_at": recent_time,
                        }
                    ]
                }

        mock_table.query.side_effect = mock_query

        result = timeout_detector_handler({}, None)

        # Should use the most recent record's updated_at, which is not stale
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
            # GSI query for started/processing tasks
            if kwargs.get("IndexName") == "operation_type-index":
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
            # Direct query for latest status - return same stale record
            else:
                return {
                    "Items": [
                        {
                            "task_id": "task-456",
                            "timestamp": stale_time,
                            "operation": "daily_journal",
                            "status": "started",
                            "updated_at": stale_time,
                        }
                    ]
                }

        mock_table.query.side_effect = mock_query

        result = timeout_detector_handler({}, None)

        # Should be marked as failed using default 600s timeout
        self.assertEqual(result["marked_failed"], 1)

        # Verify update_item was called with failed status
        update_calls = mock_table.update_item.call_args_list
        self.assertEqual(len(update_calls), 1)
        call_kwargs = update_calls[0][1]
        self.assertEqual(call_kwargs["Key"]["task_id"], "task-456")
        self.assertEqual(call_kwargs["ExpressionAttributeValues"][":status"], "failed")

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

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_does_not_mark_already_completed_task(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that tasks with 'completed' status are not marked failed."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Stale "started" record (would normally trigger timeout)
        stale_time = int(time.time()) - 700
        # Newer "completed" record
        completed_time = int(time.time()) - 100

        call_count = 0

        def mock_query(**kwargs: dict) -> dict:
            """Return stale started record via GSI, completed record via direct query."""
            nonlocal call_count
            call_count += 1

            # First call is via GSI (operation_type-index) for started/processing tasks
            if kwargs.get("IndexName") == "operation_type-index":
                expr_values = kwargs.get("ExpressionAttributeValues", {})
                if expr_values.get(":op") == "daily_sales":
                    return {
                        "Items": [
                            {
                                "task_id": "task-with-completed",
                                "timestamp": stale_time,
                                "operation": "daily_sales",
                                "status": "started",
                                "updated_at": stale_time,
                            }
                        ]
                    }
                return {"Items": []}
            # Second call is direct query to check latest status
            else:
                return {
                    "Items": [
                        {
                            "task_id": "task-with-completed",
                            "timestamp": completed_time,
                            "operation": "daily_sales",
                            "status": "completed",
                            "updated_at": completed_time,
                        }
                    ]
                }

        mock_table.query.side_effect = mock_query

        result = timeout_detector_handler({}, None)

        # Task should NOT be marked as failed because it's already completed
        self.assertEqual(result["marked_failed"], 0)
        mock_table.update_item.assert_not_called()
        mock_ws.broadcast_only.assert_not_called()

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_updates_all_stale_records_for_same_task(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that all started/processing records are updated, not just one."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # Three stale records for the same task
        base_time = int(time.time()) - 800

        def mock_query(**kwargs: dict) -> dict:
            """Return 3 stale records via GSI, no completed record via direct query."""
            if kwargs.get("IndexName") == "operation_type-index":
                expr_values = kwargs.get("ExpressionAttributeValues", {})
                if expr_values.get(":op") == "daily_sales":
                    return {
                        "Items": [
                            {
                                "task_id": "multi-record-task",
                                "timestamp": base_time,
                                "operation": "daily_sales",
                                "status": "started",
                                "updated_at": base_time,
                            },
                            {
                                "task_id": "multi-record-task",
                                "timestamp": base_time + 10,
                                "operation": "daily_sales",
                                "status": "processing",
                                "updated_at": base_time + 10,
                            },
                            {
                                "task_id": "multi-record-task",
                                "timestamp": base_time + 20,
                                "operation": "daily_sales",
                                "status": "processing",
                                "updated_at": base_time + 20,
                            },
                        ]
                    }
                return {"Items": []}
            else:
                # Direct query for latest status - return latest processing record
                return {
                    "Items": [
                        {
                            "task_id": "multi-record-task",
                            "timestamp": base_time + 20,
                            "operation": "daily_sales",
                            "status": "processing",
                            "updated_at": base_time + 20,
                        }
                    ]
                }

        mock_table.query.side_effect = mock_query

        result = timeout_detector_handler({}, None)

        # Should count as 1 marked task (not 3)
        self.assertEqual(result["marked_failed"], 1)

        # All 3 records should be updated
        update_calls = mock_table.update_item.call_args_list
        self.assertEqual(len(update_calls), 3)

        # Verify all updates are for the same task_id but different timestamps
        updated_timestamps = set()
        for call in update_calls:
            call_kwargs = call[1]
            self.assertEqual(call_kwargs["Key"]["task_id"], "multi-record-task")
            self.assertEqual(
                call_kwargs["ExpressionAttributeValues"][":status"], "failed"
            )
            updated_timestamps.add(call_kwargs["Key"]["timestamp"])

        # Should have 3 different timestamps
        self.assertEqual(len(updated_timestamps), 3)

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_uses_broadcast_only_not_broadcast_status(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that timeout detector uses broadcast_only to avoid creating records."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        stale_time = int(time.time()) - 700

        def mock_query(**kwargs: dict) -> dict:
            """Return stale task via GSI, still in-progress via direct query."""
            if kwargs.get("IndexName") == "operation_type-index":
                expr_values = kwargs.get("ExpressionAttributeValues", {})
                if expr_values.get(":op") == "daily_sales":
                    return {
                        "Items": [
                            {
                                "task_id": "broadcast-test-task",
                                "timestamp": stale_time,
                                "operation": "daily_sales",
                                "status": "started",
                                "updated_at": stale_time,
                            }
                        ]
                    }
                return {"Items": []}
            else:
                # Direct query returns same stale record (no completion)
                return {
                    "Items": [
                        {
                            "task_id": "broadcast-test-task",
                            "timestamp": stale_time,
                            "operation": "daily_sales",
                            "status": "started",
                            "updated_at": stale_time,
                        }
                    ]
                }

        mock_table.query.side_effect = mock_query

        result = timeout_detector_handler({}, None)

        self.assertEqual(result["marked_failed"], 1)

        # broadcast_only should be called (not broadcast_status)
        mock_ws.broadcast_only.assert_called_once()
        call_args = mock_ws.broadcast_only.call_args
        self.assertEqual(call_args[1]["task_id"], "broadcast-test-task")
        self.assertEqual(call_args[1]["operation"], "daily_sales")
        self.assertEqual(call_args[1]["status"], "failed")
        self.assertIn("timed out", call_args[1]["error"])

        # broadcast_status should NOT be called
        mock_ws.broadcast_status.assert_not_called()

    @patch("lambda_function.WebSocketManager")
    @patch("lambda_function.dynamodb")
    def test_skips_already_failed_task(
        self,
        mock_dynamodb: MagicMock,
        mock_ws_manager_class: MagicMock,
    ) -> None:
        """Test that tasks already marked as failed are skipped."""
        from lambda_function import timeout_detector_handler

        mock_ws = MagicMock()
        mock_ws_manager_class.return_value = mock_ws

        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        stale_time = int(time.time()) - 700
        failed_time = int(time.time()) - 50

        def mock_query(**kwargs: dict) -> dict:
            """Return stale started record via GSI, failed record via direct query."""
            if kwargs.get("IndexName") == "operation_type-index":
                expr_values = kwargs.get("ExpressionAttributeValues", {})
                if expr_values.get(":op") == "daily_sales":
                    return {
                        "Items": [
                            {
                                "task_id": "already-failed-task",
                                "timestamp": stale_time,
                                "operation": "daily_sales",
                                "status": "started",
                                "updated_at": stale_time,
                            }
                        ]
                    }
                return {"Items": []}
            else:
                # Latest record shows task already failed
                return {
                    "Items": [
                        {
                            "task_id": "already-failed-task",
                            "timestamp": failed_time,
                            "operation": "daily_sales",
                            "status": "failed",
                            "updated_at": failed_time,
                        }
                    ]
                }

        mock_table.query.side_effect = mock_query

        result = timeout_detector_handler({}, None)

        # Task should NOT be marked as failed again
        self.assertEqual(result["marked_failed"], 0)
        mock_table.update_item.assert_not_called()


if __name__ == "__main__":
    unittest.main()
