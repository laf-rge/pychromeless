"""Tests for websocket_handlers.py exception handling."""

import json
import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError


class TestWebSocketHandlersExceptionHandling(unittest.TestCase):
    """Test that ClientError exceptions are properly caught and handled."""

    def _create_client_error(self, code: str = "ValidationException") -> ClientError:
        """Helper to create a ClientError for testing."""
        return ClientError(
            error_response={"Error": {"Code": code, "Message": "Test error"}},
            operation_name="TestOperation",
        )

    def _create_event(self, connection_id: str = "test-connection-123") -> dict:
        """Helper to create a mock API Gateway WebSocket event."""
        return {
            "requestContext": {
                "connectionId": connection_id,
                "identity": {
                    "sourceIp": "127.0.0.1",
                    "userAgent": "test-agent",
                },
            },
            "body": "{}",
        }

    @patch("websocket_handlers.table")
    def test_connect_handler_handles_client_error(self, mock_table: MagicMock) -> None:
        """Test that connect_handler catches ClientError and returns 500."""
        from websocket_handlers import connect_handler

        # Set up mock table that raises ClientError on put_item
        mock_table.put_item.side_effect = self._create_client_error()

        event = self._create_event()
        result = connect_handler(event, None)

        # Should return 500 status, not raise exception
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "Failed to connect")

    @patch("websocket_handlers.table")
    def test_connect_handler_success(self, mock_table: MagicMock) -> None:
        """Test that connect_handler works correctly on success."""
        from websocket_handlers import connect_handler

        mock_table.put_item.return_value = {}

        event = self._create_event()
        result = connect_handler(event, None)

        # Should return 200 status
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "Connected")
        mock_table.put_item.assert_called_once()

    @patch("websocket_handlers.table")
    def test_disconnect_handler_handles_client_error(
        self, mock_table: MagicMock
    ) -> None:
        """Test that disconnect_handler catches ClientError and returns 500."""
        from websocket_handlers import disconnect_handler

        # Set up mock table that raises ClientError on delete_item
        mock_table.delete_item.side_effect = self._create_client_error()

        event = self._create_event()
        result = disconnect_handler(event, None)

        # Should return 500 status, not raise exception
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "Failed to disconnect")

    @patch("websocket_handlers.table")
    def test_disconnect_handler_success(self, mock_table: MagicMock) -> None:
        """Test that disconnect_handler works correctly on success."""
        from websocket_handlers import disconnect_handler

        mock_table.delete_item.return_value = {}

        event = self._create_event()
        result = disconnect_handler(event, None)

        # Should return 200 status
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "Disconnected")
        mock_table.delete_item.assert_called_once()

    @patch("websocket_handlers.table", None)
    def test_connect_handler_no_table_configured(self) -> None:
        """Test that connect_handler returns 500 when table is not configured."""
        from websocket_handlers import connect_handler

        event = self._create_event()
        result = connect_handler(event, None)

        # Should return 500 status
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "Database not configured")

    @patch("websocket_handlers.table", None)
    def test_disconnect_handler_no_table_configured(self) -> None:
        """Test that disconnect_handler returns 500 when table is not configured."""
        from websocket_handlers import disconnect_handler

        event = self._create_event()
        result = disconnect_handler(event, None)

        # Should return 500 status
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "Database not configured")

    @patch("websocket_handlers.table")
    def test_default_handler_ping_message(self, mock_table: MagicMock) -> None:
        """Test that default_handler handles ping messages."""
        from websocket_handlers import default_handler

        mock_table.update_item.return_value = {}

        event = self._create_event()
        event["body"] = json.dumps({"type": "ping"})
        result = default_handler(event, None)

        # Should return pong response
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["type"], "pong")


if __name__ == "__main__":
    unittest.main()
