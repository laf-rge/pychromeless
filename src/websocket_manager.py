import json
import logging
import os
import time
from typing import Any, Dict, Optional, Protocol, cast

import boto3
from mypy_boto3_apigatewaymanagementapi.client import ApiGatewayManagementApiClient
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource

from operation_types import OperationType

logger = logging.getLogger(__name__)


class DynamoDBTable(Protocol):
    def put_item(self, Item: Dict[str, Any]) -> Dict[str, Any]: ...
    def get_item(self, Key: Dict[str, Any]) -> Dict[str, Any]: ...
    def update_item(
        self,
        Key: Dict[str, Any],
        UpdateExpression: str,
        ExpressionAttributeNames: Dict[str, str],
        ExpressionAttributeValues: Dict[str, Any],
    ) -> Dict[str, Any]: ...
    def delete_item(self, Key: Dict[str, Any]) -> Dict[str, Any]: ...
    def scan(
        self,
        FilterExpression: Optional[str] = None,
        ExpressionAttributeValues: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]: ...


class WebSocketManager:
    apigateway: ApiGatewayManagementApiClient
    dynamodb: DynamoDBServiceResource
    table: Any  # DynamoDB Table type

    def __init__(self):
        self.apigateway = cast(
            ApiGatewayManagementApiClient,
            boto3.client(
                "apigatewaymanagementapi",
                endpoint_url=os.environ.get(
                    "WEBSOCKET_ENDPOINT",
                    "https://xxxxx.execute-api.us-east-2.amazonaws.com/production",
                ),
            ),
        )
        self.dynamodb = cast(DynamoDBServiceResource, boto3.resource("dynamodb"))
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
        current_time = int(time.time())

        # Standardize result format to always include success boolean
        standardized_result = None
        if result is not None:
            standardized_result = self._standardize_result_format(result, status)

        # Construct the message to match API format
        message = {
            "type": "task_status",
            "payload": {
                "task_id": task_id,
                "operation": operation,
                "status": status,
                "progress": progress,
                "result": standardized_result,
                "error": error,
                "created_at": current_time,
                "updated_at": current_time,
            },
        }

        # Get all active connections
        response = self.table.scan()
        connections = response.get("Items", [])

        # Send to each connection
        for connection in connections:
            try:
                self.apigateway.post_to_connection(
                    ConnectionId=str(connection["connection_id"]),
                    Data=json.dumps(message),
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

    def _standardize_result_format(self, result: Dict, status: str) -> Dict:
        """Standardize result format to ensure consistent structure with success boolean

        Args:
            result: Original result dictionary
            status: Current task status to determine success

        Returns:
            Standardized result dictionary with success boolean and consistent structure
        """
        # Determine success based on status
        success = status in ["completed", "completed_with_errors"]

        # Create standardized result
        standardized = {
            "success": success,
            "message": result.get("summary", "Operation completed"),
        }

        # Preserve existing fields that match frontend interface
        if "processed_dates" in result:
            standardized["processed_dates"] = result["processed_dates"]
        if "successful_stores" in result:
            standardized["successful_stores"] = result["successful_stores"]
        if "failed_stores" in result:
            standardized["failed_stores"] = result["failed_stores"]
        if "total_stores" in result:
            standardized["total_stores"] = result["total_stores"]
        if "success_count" in result:
            standardized["success_count"] = result["success_count"]
        if "failure_count" in result:
            standardized["failure_count"] = result["failure_count"]
        if "summary" in result:
            standardized["summary"] = result["summary"]

        return standardized


class TaskManager:
    dynamodb: DynamoDBServiceResource
    table: Any  # DynamoDB Table type
    gatewayapi: ApiGatewayManagementApiClient

    def __init__(self, table_name: str):
        self.dynamodb = cast(DynamoDBServiceResource, boto3.resource("dynamodb"))
        self.table = self.dynamodb.Table(table_name)
        self.gatewayapi = cast(
            ApiGatewayManagementApiClient,
            boto3.client("apigatewaymanagementapi"),
        )

    def create_task(
        self,
        task_id: str,
        operation: OperationType,
        status: str = "started",
        progress: Optional[Dict] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Create a new task with TTL"""
        current_time = int(time.time())
        ttl = current_time + operation.ttl_seconds

        task = {
            "task_id": task_id,
            "operation": operation.value,  # Store the enum value
            "status": status,
            "progress": progress,
            "result": result,
            "error": error,
            "created_at": current_time,
            "updated_at": current_time,
            "ttl": ttl,
        }

        self.table.put_item(Item=task)
        self._broadcast_status(task)

    def update_progress(
        self,
        task_id: str,
        operation: OperationType,
        progress: Dict,
        status: str = "processing",
    ) -> None:
        """Update task progress"""
        current_time = int(time.time())
        ttl = current_time + operation.ttl_seconds

        task = {
            "task_id": task_id,
            "operation": operation.value,
            "status": status,
            "progress": progress,
            "updated_at": current_time,
            "ttl": ttl,
        }

        self.table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET #status = :status, #progress = :progress, #updated_at = :updated_at, #ttl = :ttl",
            ExpressionAttributeNames={
                "#status": "status",
                "#progress": "progress",
                "#updated_at": "updated_at",
                "#ttl": "ttl",
            },
            ExpressionAttributeValues={
                ":status": status,
                ":progress": progress,
                ":updated_at": current_time,
                ":ttl": ttl,
            },
        )

        self._broadcast_status(task)

    def complete_task(
        self,
        task_id: str,
        operation: OperationType,
        result: Dict,
        status: str = "completed",
    ) -> None:
        """Mark task as completed with results"""
        current_time = int(time.time())
        ttl = current_time + operation.ttl_seconds

        task = {
            "task_id": task_id,
            "operation": operation.value,
            "status": status,
            "result": result,
            "updated_at": current_time,
            "ttl": ttl,
        }

        self.table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET #status = :status, #result = :result, #updated_at = :updated_at, #ttl = :ttl",
            ExpressionAttributeNames={
                "#status": "status",
                "#result": "result",
                "#updated_at": "updated_at",
                "#ttl": "ttl",
            },
            ExpressionAttributeValues={
                ":status": status,
                ":result": result,
                ":updated_at": current_time,
                ":ttl": ttl,
            },
        )

        self._broadcast_status(task)

    def fail_task(
        self,
        task_id: str,
        operation: OperationType,
        error: str,
        status: str = "failed",
    ) -> None:
        """Mark task as failed with error message"""
        current_time = int(time.time())
        ttl = current_time + operation.ttl_seconds

        task = {
            "task_id": task_id,
            "operation": operation.value,
            "status": status,
            "error": error,
            "updated_at": current_time,
            "ttl": ttl,
        }

        self.table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET #status = :status, #error = :error, #updated_at = :updated_at, #ttl = :ttl",
            ExpressionAttributeNames={
                "#status": "status",
                "#error": "error",
                "#updated_at": "updated_at",
                "#ttl": "ttl",
            },
            ExpressionAttributeValues={
                ":status": status,
                ":error": error,
                ":updated_at": current_time,
                ":ttl": ttl,
            },
        )

        self._broadcast_status(task)

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current task status"""
        response = self.table.get_item(Key={"task_id": task_id})
        return response.get("Item")

    def _broadcast_status(self, task: Dict) -> None:
        """Broadcast task status to all connected clients"""
        try:
            # Get all active connections
            response = self.table.scan(
                FilterExpression="begins_with(connection_id, :prefix)",
                ExpressionAttributeValues={":prefix": "connection_"},
            )

            # Broadcast to each connection
            for item in response.get("Items", []):
                connection_id = str(item["connection_id"])
                try:
                    self.gatewayapi.post_to_connection(
                        ConnectionId=connection_id,
                        Data=json.dumps({"type": "task_update", "task": task}),
                    )
                except Exception as e:
                    print(f"Error broadcasting to {connection_id}: {str(e)}")
                    # Remove stale connections
                    self.table.delete_item(Key={"connection_id": connection_id})

        except Exception as e:
            print(f"Error broadcasting task status: {str(e)}")
