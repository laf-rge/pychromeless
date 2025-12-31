import { X } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "../ui/alert";
import { TaskInfo } from "../../stores/taskStore";
import {
  getStatusVariant,
  getStatusIcon,
  getStatusTitle,
  calculateProgressPercent,
} from "../../utils/taskUtils";

interface TaskNotificationCardProps {
  task: TaskInfo;
  onDismiss: () => void;
}

/**
 * Individual task notification card
 * Displays operation name, progress, status with color-coded border
 */
export function TaskNotificationCard({ task, onDismiss }: TaskNotificationCardProps) {
  const statusVariant = getStatusVariant(task.status);
  const progressPercent = calculateProgressPercent(task.progress);

  return (
    <Alert
      variant={statusVariant}
      className="shadow-lg border-l-4 animate-in slide-in-from-right duration-300 relative"
      style={{
        borderLeftColor: task.color,
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <AlertTitle className="flex items-center gap-2 mb-2">
            {getStatusIcon(task.status)}
            <span className="truncate">{task.operationDisplayName}</span>
          </AlertTitle>
          <AlertDescription className="space-y-2">
            {/* Progress bar and message */}
            {task.progress && (
              <div className="space-y-1">
                <p className="text-sm">{task.progress.message}</p>
                <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                  <div
                    className="h-2 rounded-full transition-all duration-300 ease-in-out"
                    style={{
                      width: `${progressPercent}%`,
                      backgroundColor: task.color,
                    }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  {task.progress.current}/{task.progress.total} ({progressPercent}%)
                </p>
              </div>
            )}

            {/* Error message */}
            {task.error && (
              <div className="mt-2">
                <p className="text-sm font-medium text-destructive">Error:</p>
                <p className="text-sm text-destructive">{task.error}</p>
              </div>
            )}

            {/* Result message */}
            {task.result?.message && (
              <div className="mt-2">
                <p className="text-sm">{task.result.message}</p>
                {task.result.failed_stores && task.result.failed_stores.length > 0 && (
                  <p className="text-xs text-destructive mt-1">
                    Failed stores: {task.result.failed_stores.join(", ")}
                  </p>
                )}
              </div>
            )}

            {/* Status without progress */}
            {!task.progress && !task.error && !task.result?.message && (
              <p className="text-sm">{getStatusTitle(task.status)}</p>
            )}
          </AlertDescription>
        </div>

        {/* Dismiss button */}
        <button
          onClick={onDismiss}
          className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors p-1 rounded-sm hover:bg-accent"
          aria-label="Dismiss notification"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </Alert>
  );
}
