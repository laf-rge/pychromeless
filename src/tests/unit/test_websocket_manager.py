"""Tests for websocket_manager.py"""

import json
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestWebSocketManagerDecimalSerialization(unittest.TestCase):
    """Test that WebSocketManager correctly serializes Decimal values."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "CONNECTIONS_TABLE": "test-connections",
                "TASK_STATES_TABLE": "test-task-states",
                "WEBSOCKET_ENDPOINT": "https://test.execute-api.us-east-2.amazonaws.com/prod",
            },
        )
        self.env_patcher.start()

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.env_patcher.stop()

    @patch("websocket_manager.boto3")
    def test_broadcast_status_handles_decimal_values(
        self,
        mock_boto3: MagicMock,
    ) -> None:
        """Test that broadcast_status serializes Decimal values without error."""
        from websocket_manager import WebSocketManager

        # Set up mocks
        mock_dynamodb = MagicMock()
        mock_boto3.resource.return_value = mock_dynamodb

        mock_connections_table = MagicMock()
        mock_task_states_table = MagicMock()

        def mock_table(name: str) -> MagicMock:
            if "connections" in name.lower():
                return mock_connections_table
            return mock_task_states_table

        mock_dynamodb.Table.side_effect = mock_table

        mock_apigateway = MagicMock()
        mock_boto3.client.return_value = mock_apigateway

        # Mock existing task query (returns Decimal values from DynamoDB)
        mock_task_states_table.query.return_value = {
            "Items": [
                {
                    "task_id": "test-123",
                    "timestamp": Decimal("1705520000"),
                    "created_at": Decimal("1705520000"),
                    "updated_at": Decimal("1705520000"),
                }
            ]
        }

        # Mock connections scan
        mock_connections_table.scan.return_value = {
            "Items": [{"connection_id": "test-connection-1"}]
        }

        ws_manager = WebSocketManager()

        # Call broadcast_status with a result containing Decimal values
        # This should NOT raise "Object of type Decimal is not JSON serializable"
        ws_manager.broadcast_status(
            task_id="test-123",
            operation="daily_sales",
            status="completed",
            progress={"current": Decimal("5"), "total": Decimal("10")},
            result={
                "amount": Decimal("1234.56"),
                "count": Decimal("42"),
            },
        )

        # Verify post_to_connection was called
        mock_apigateway.post_to_connection.assert_called_once()

        # Verify the Data can be parsed as valid JSON
        call_args = mock_apigateway.post_to_connection.call_args
        data = call_args[1]["Data"]
        parsed = json.loads(data)

        # Verify structure
        self.assertEqual(parsed["type"], "task_status")
        self.assertEqual(parsed["payload"]["task_id"], "test-123")
        self.assertEqual(parsed["payload"]["status"], "completed")

    @patch("websocket_manager.boto3")
    def test_broadcast_status_converts_decimal_to_number(
        self,
        mock_boto3: MagicMock,
    ) -> None:
        """Test that Decimal values are converted to int/float in JSON output."""
        from websocket_manager import WebSocketManager

        # Set up mocks
        mock_dynamodb = MagicMock()
        mock_boto3.resource.return_value = mock_dynamodb

        mock_connections_table = MagicMock()
        mock_task_states_table = MagicMock()

        def mock_table(name: str) -> MagicMock:
            if "connections" in name.lower():
                return mock_connections_table
            return mock_task_states_table

        mock_dynamodb.Table.side_effect = mock_table

        mock_apigateway = MagicMock()
        mock_boto3.client.return_value = mock_apigateway

        mock_task_states_table.query.return_value = {"Items": []}
        mock_connections_table.scan.return_value = {
            "Items": [{"connection_id": "test-connection-1"}]
        }

        ws_manager = WebSocketManager()

        ws_manager.broadcast_status(
            task_id="test-123",
            operation="daily_sales",
            status="processing",
            progress={
                "current_step": Decimal("3"),
                "total_steps": Decimal("10"),
                "percentage": Decimal("30.5"),
            },
        )

        # Get the serialized data
        call_args = mock_apigateway.post_to_connection.call_args
        data = call_args[1]["Data"]
        parsed = json.loads(data)

        # Verify Decimals were converted to numbers (not strings)
        progress = parsed["payload"]["progress"]
        self.assertIsInstance(progress["current_step"], (int, float))
        self.assertIsInstance(progress["total_steps"], (int, float))
        self.assertIsInstance(progress["percentage"], float)


if __name__ == "__main__":
    unittest.main()
