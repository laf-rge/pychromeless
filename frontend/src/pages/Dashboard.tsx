import { useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { useTaskStore } from "../stores/taskStore";
import { TaskHistoryCard } from "../components/dashboard/TaskHistoryCard";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { OperationType, OperationDisplayNames } from "../services/WebSocketService";
import { TaskStatusType } from "../services/TaskStatusService";

export function DashboardPage() {
  const {
    activeTasks,
    completedTasks,
    failedTasks,
    loadTaskHistory,
    isLoadingHistory,
    historyError,
  } = useTaskStore();

  const [filterOperation, setFilterOperation] = useState<OperationType | "all">("all");
  const [filterStatus, setFilterStatus] = useState<TaskStatusType | "all">("all");

  // Combine all tasks
  const allTasks = useMemo(() => {
    const tasks = [
      ...Array.from(activeTasks.values()),
      ...Array.from(completedTasks.values()),
      ...Array.from(failedTasks.values()),
    ];

    // Apply filters
    let filtered = tasks;

    if (filterOperation !== "all") {
      filtered = filtered.filter((task) => task.operation === filterOperation);
    }

    if (filterStatus !== "all") {
      filtered = filtered.filter((task) => task.status === filterStatus);
    }

    // Sort by updated_at descending (newest first)
    return filtered.sort((a, b) => b.updated_at - a.updated_at);
  }, [activeTasks, completedTasks, failedTasks, filterOperation, filterStatus]);

  // Group tasks by operation
  const tasksByOperation = useMemo(() => {
    const grouped: Record<string, typeof allTasks> = {};

    allTasks.forEach((task) => {
      const key = task.operationDisplayName;
      if (!grouped[key]) {
        grouped[key] = [];
      }
      grouped[key].push(task);
    });

    return grouped;
  }, [allTasks]);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Task History</h1>
          <p className="text-muted-foreground mt-1">
            View and monitor all operation tasks
          </p>
        </div>
        <button
          onClick={() => loadTaskHistory()}
          disabled={isLoadingHistory}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw
            className={`h-4 w-4 ${isLoadingHistory ? "animate-spin" : ""}`}
          />
          {isLoadingHistory ? "Loading..." : "Refresh"}
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Tasks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeTasks.size}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {completedTasks.size}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {failedTasks.size}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{allTasks.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Error Display */}
      {historyError && (
        <div className="rounded-md bg-red-50 border border-red-200 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Failed to load task history
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{historyError}</p>
              </div>
              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => loadTaskHistory()}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div>
          <label
            htmlFor="operation-filter"
            className="block text-sm font-medium mb-1"
          >
            Operation
          </label>
          <select
            id="operation-filter"
            value={filterOperation}
            onChange={(e) =>
              setFilterOperation(e.target.value as OperationType | "all")
            }
            className="px-3 py-2 border rounded-md bg-background"
          >
            <option value="all">All Operations</option>
            {Object.entries(OperationDisplayNames).map(([key, name]) => (
              <option key={key} value={key}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="status-filter" className="block text-sm font-medium mb-1">
            Status
          </label>
          <select
            id="status-filter"
            value={filterStatus}
            onChange={(e) =>
              setFilterStatus(e.target.value as TaskStatusType | "all")
            }
            className="px-3 py-2 border rounded-md bg-background"
          >
            <option value="all">All Statuses</option>
            <option value="started">Started</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="completed_with_errors">Completed with Errors</option>
            <option value="failed">Failed</option>
            <option value="error">Error</option>
          </select>
        </div>
      </div>

      {/* Task List */}
      {allTasks.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            {isLoadingHistory
              ? "Loading task history..."
              : "No tasks found matching the selected filters"}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {filterOperation === "all" ? (
            // Group by operation when showing all
            Object.entries(tasksByOperation).map(([operationName, tasks]) => (
              <div key={operationName}>
                <h2 className="text-xl font-semibold mb-3">{operationName}</h2>
                <div className="space-y-2">
                  {tasks.map((task) => (
                    <TaskHistoryCard key={task.task_id} task={task} />
                  ))}
                </div>
              </div>
            ))
          ) : (
            // Show flat list when filtering by specific operation
            <div className="space-y-2">
              {allTasks.map((task) => (
                <TaskHistoryCard key={task.task_id} task={task} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
