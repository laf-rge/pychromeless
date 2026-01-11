import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { TaskInfo } from "../../stores/taskStore";
import {
  getStatusIcon,
  getStatusBadgeVariant,
  formatRelativeTime,
} from "../../utils/taskUtils";
import { cn } from "../../utils/cn";

interface TaskHistoryCardProps {
  task: TaskInfo;
}

/**
 * Expandable task history card for Dashboard
 * Shows task summary with expandable details
 */
export function TaskHistoryCard({ task }: TaskHistoryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const badgeVariant = getStatusBadgeVariant(task.status);
  const badgeClasses = cn(
    "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
    {
      "bg-green-100 text-green-800": badgeVariant === "success",
      "bg-yellow-100 text-yellow-800": badgeVariant === "warning",
      "bg-red-100 text-red-800": badgeVariant === "destructive",
      "bg-blue-100 text-blue-800": badgeVariant === "default",
    }
  );

  return (
    <Card
      className="hover:shadow-md transition-shadow border-l-4"
      style={{ borderLeftColor: task.color }}
    >
      <CardContent className="p-4">
        {/* Header area - clickable to toggle expansion */}
        <div
          className="flex items-center justify-between gap-3 cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {getStatusIcon(task.status)}
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{task.operationDisplayName}</div>
              <div className="text-sm text-muted-foreground">
                {formatRelativeTime(task.updated_at)}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className={badgeClasses}>{task.status}</span>
            <ChevronDown
              className={cn(
                "h-5 w-5 transition-transform text-muted-foreground",
                isExpanded && "rotate-180"
              )}
            />
          </div>
        </div>

        {/* Expanded content - click does not collapse, allows text selection */}
        {isExpanded && (
          <div
            className="mt-4 space-y-3 border-t pt-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Task ID */}
            <div>
              <span className="text-sm font-medium">Task ID:</span>
              <code className="ml-2 text-xs bg-muted px-2 py-1 rounded">
                {task.task_id}
              </code>
            </div>

            {/* Progress */}
            {task.progress && (
              <div>
                <span className="text-sm font-medium">Progress:</span>
                <div className="mt-1 space-y-1">
                  <p className="text-sm">{task.progress.message}</p>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{
                        width: `${
                          (task.progress.current / task.progress.total) * 100
                        }%`,
                        backgroundColor: task.color,
                      }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {task.progress.current}/{task.progress.total} (
                    {Math.round(
                      (task.progress.current / task.progress.total) * 100
                    )}
                    %)
                  </p>
                </div>
              </div>
            )}

            {/* Result */}
            {task.result && (
              <div>
                <span className="text-sm font-medium">Result:</span>
                <div className="mt-1">
                  {task.result.message && (
                    <p className="text-sm">{task.result.message}</p>
                  )}
                  {task.result.failed_stores &&
                    task.result.failed_stores.length > 0 && (
                      <p className="text-sm text-destructive mt-1">
                        Failed stores: {task.result.failed_stores.join(", ")}
                      </p>
                    )}
                  {task.result.successful_stores &&
                    task.result.successful_stores.length > 0 && (
                      <p className="text-sm text-green-600 mt-1">
                        Successful stores:{" "}
                        {task.result.successful_stores.join(", ")}
                      </p>
                    )}
                  {/* Show full result as JSON if it has more data */}
                  {Object.keys(task.result).length > 2 && (
                    <details className="mt-2">
                      <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                        Show full result
                      </summary>
                      <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                        {JSON.stringify(task.result, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            )}

            {/* Error */}
            {task.error && (
              <div>
                <span className="text-sm font-medium text-destructive">Error:</span>
                <p className="text-sm text-destructive mt-1">{task.error}</p>
              </div>
            )}

            {/* Timestamps */}
            <div className="text-xs text-muted-foreground space-y-1">
              <div>
                Created: {new Date(task.created_at).toLocaleString()}
              </div>
              <div>
                Updated: {new Date(task.updated_at).toLocaleString()}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
