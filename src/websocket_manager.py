import os
import json
import boto3
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.apigateway = boto3.client(
            "apigatewaymanagementapi",
            endpoint_url=os.environ.get(
                "WEBSOCKET_ENDPOINT",
                "https://xxxxx.execute-api.us-east-2.amazonaws.com/production",
            ),
        )
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(os.environ["CONNECTIONS_TABLE"])

    def broadcast_status(
        self,
        task_id: str,
        operation: str,
        status: str,  # Now supports: "started", "processing", "error", "completed", "completed_with_errors", "failed"
        progress: Optional[Dict] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Broadcast status update to all connected clients

        Args:
            task_id: Unique identifier for the task
            operation: Name of the operation (e.g., "daily_sales")
            status: Current status of the task. One of:
                   - "started": Task has begun
                   - "processing": Task is in progress
                   - "error": An error occurred for a specific store but task continues
                   - "completed": Task completed successfully
                   - "completed_with_errors": Task completed but some stores failed
                   - "failed": Task failed completely
            progress: Optional progress information
            result: Optional result data
            error: Optional error message
        """
        # Construct the message
        message = {
            "type": "task_status",
            "payload": {
                "task_id": task_id,
                "operation": operation,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        # Add optional fields if present
        if progress:
            message["payload"]["progress"] = progress
        if result:
            message["payload"]["result"] = result
        if error:
            message["payload"]["error"] = error

        # Get all active connections
        response = self.table.scan()
        connections = response.get("Items", [])

        # Send to each connection
        for connection in connections:
            try:
                self.apigateway.post_to_connection(
                    ConnectionId=connection["connection_id"], Data=json.dumps(message)
                )
            except self.apigateway.exceptions.GoneException:
                # Connection is no longer valid, remove it
                logger.info(f"Removing stale connection: {connection['connection_id']}")
                try:
                    self.table.delete_item(
                        Key={"connection_id": connection["connection_id"]}
                    )
                except Exception as e:
                    logger.error(f"Error removing stale connection: {str(e)}")
            except Exception as e:
                logger.warning(
                    "Failed to send to connection",
                    extra={
                        "connection_id": connection["connection_id"],
                        "error": str(e),
                    },
                )
