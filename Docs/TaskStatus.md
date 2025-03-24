# Task Status System Documentation

## Overview

The task status system provides real-time updates via WebSocket and REST API endpoints for tracking background tasks. This system is used for operations like daily sales processing, invoice syncing, and other long-running tasks.

## WebSocket Interface

### Connection

```javascript
const ws = new WebSocket("wss://your-api-gateway-url/test");
```

### Message Types

All messages follow this structure:

```typescript
interface WebSocketMessage {
  type: string;
  payload: TaskStatus;
}

interface TaskStatus {
  task_id: string;
  operation: string;
  status: TaskStatusType;
  progress?: {
    current: number;
    total: number;
    message: string;
  };
  result?: any;
  error?: string;
  created_at: number; // Unix timestamp
  updated_at: number; // Unix timestamp
}

type TaskStatusType =
  | "started" // Task has begun
  | "processing" // Task is in progress
  | "error" // Error occurred but task continues
  | "completed" // Task completed successfully
  | "completed_with_errors" // Task completed with some failures
  | "failed"; // Task failed completely
```

### Example Usage

```javascript
const ws = new WebSocket("wss://your-api-gateway-url/test");

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === "task_status") {
    const task = message.payload;

    switch (task.status) {
      case "started":
        console.log(`Task ${task.task_id} started`);
        break;

      case "processing":
        console.log(
          `Progress: ${task.progress.current}/${task.progress.total}`
        );
        break;

      case "completed":
        console.log("Task completed:", task.result);
        break;

      case "failed":
        console.error("Task failed:", task.error);
        break;
    }
  }
};
```

## REST API Interface

### Endpoints

#### 1. Get Task by ID

```http
GET /task-status/{task_id}
```

**Response:**

```json
{
  "task_id": "string",
  "operation": "string",
  "status": "string",
  "progress": {
    "current": number,
    "total": number,
    "message": "string"
  },
  "result": any,
  "error": "string",
  "created_at": number,
  "updated_at": number
}
```

#### 2. Get Tasks by Operation Type

```http
GET /task-status?operation={operation_type}
```

**Response:**

```json
[
  {
    "task_id": "string",
    "operation": "string",
    "status": "string",
    "progress": { ... },
    "result": any,
    "error": "string",
    "created_at": number,
    "updated_at": number
  }
]
```

#### 3. Get All Tasks

```http
GET /task-status
```

**Response:**

```json
[
  {
    "task_id": "string",
    "operation": "string",
    "status": "string",
    "progress": { ... },
    "result": any,
    "error": "string",
    "created_at": number,
    "updated_at": number
  }
]
```

### Example Usage

```typescript
interface TaskStatus {
  task_id: string;
  operation: string;
  status: TaskStatusType;
  progress?: {
    current: number;
    total: number;
    message: string;
  };
  result?: any;
  error?: string;
  created_at: number;
  updated_at: number;
}

// Get specific task
const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await fetch(`/task-status/${taskId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch task status");
  }
  return response.json();
};

// Get tasks by operation
const getTasksByOperation = async (
  operation: string
): Promise<TaskStatus[]> => {
  const response = await fetch(`/task-status?operation=${operation}`);
  if (!response.ok) {
    throw new Error("Failed to fetch tasks");
  }
  return response.json();
};

// Get all tasks
const getAllTasks = async (): Promise<TaskStatus[]> => {
  const response = await fetch("/task-status");
  if (!response.ok) {
    throw new Error("Failed to fetch tasks");
  }
  return response.json();
};
```

## Common Fields

### Task Status Values

- `started`: Task has begun
- `processing`: Task is in progress (includes progress information)
- `error`: An error occurred but the task continues
- `completed`: Task completed successfully (includes result data)
- `completed_with_errors`: Task completed but some operations failed
- `failed`: Task failed completely (includes error message)

### Operation Types

- `daily_sales`: Daily sales processing
- `invoice_sync`: Invoice synchronization
- `update_food_handler_pdfs`: Food handler PDF updates
- `transform_tips`: Tips transformation
- `get_mpvs`: Meal period violations
- `get_food_handler_links`: Food handler PDF links
- `email_tips`: Tips email generation

### Progress Information

When status is "processing", the progress object includes:

- `current`: Current progress (number)
- `total`: Total steps (number)
- `message`: Human-readable progress message

### Timestamps

- `created_at`: Unix timestamp when the task was created
- `updated_at`: Unix timestamp of the last status update

## Notes

- All endpoints require authentication via MSAL token
- WebSocket connections should implement reconnection logic
- Tasks are automatically cleaned up after their TTL expires
- Request IDs are included in response headers for tracking
- All timestamps are Unix timestamps (seconds since epoch)
