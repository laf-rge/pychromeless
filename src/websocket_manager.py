import os
import json
import boto3
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.apigateway = boto3.client("apigatewaymanagementapi")
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(os.environ["CONNECTIONS_TABLE"])

    def _get_endpoint(self, domain_name: str, stage: str) -> str:
        return f"https://{domain_name}/{stage}"

    def broadcast_status(
        self,
        task_id: str,
        operation: str,
        status: str,
        progress: Optional[Dict] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Broadcast status update to all connected clients"""

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
            except Exception as e:
                logger.warning(
                    "Failed to send to connection",
                    extra={
                        "connection_id": connection["connection_id"],
                        "error": str(e),
                    },
                )
