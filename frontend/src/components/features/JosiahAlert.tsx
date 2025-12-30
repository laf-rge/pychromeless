import { AxiosError } from "axios";
import { Alert, AlertTitle, AlertDescription } from "../ui/alert";
import { cn } from "../../utils/cn";

interface TaskStatus {
  status?:
    | "started"
    | "processing"
    | "completed"
    | "completed_with_errors"
    | "failed";
  progress?: {
    current: number;
    total: number;
    message: string;
  };
  error?: string;
  result?: {
    success: boolean;
    message: string;
    failed_stores?: string[];
  };
}

interface JosiahAlertProps {
  error?: AxiosError;
  isSuccess?: boolean;
  successMessage: string;
  taskStatus?: TaskStatus;
}

export function JosiahAlert({
  error,
  isSuccess,
  successMessage,
  taskStatus,
}: JosiahAlertProps) {
  if (taskStatus?.status) {
    const statusMap: Record<string, "default" | "destructive" | "warning" | "success"> = {
      started: "default",
      processing: "default",
      completed: "success",
      completed_with_errors: "warning",
      failed: "destructive",
      error: "destructive",
    };
    const variant = statusMap[taskStatus.status] || "default";

    const title = {
      started: "Processing Started",
      processing: "Processing in Progress",
      completed: "Processing Complete",
      completed_with_errors: "Processing Complete with Errors",
      failed: "Processing Failed",
    }[taskStatus.status];

    const progressPercent = taskStatus.progress
      ? (taskStatus.progress.current / taskStatus.progress.total) * 100
      : 0;

    return (
      <Alert variant={variant} className="mb-4">
        <AlertTitle>{title}</AlertTitle>
        <AlertDescription>
          {taskStatus.progress && (
            <div className="mt-2 space-y-2">
              <p>{taskStatus.progress.message}</p>
              <div className="w-full bg-secondary rounded-full h-2">
                <div
                  className={cn(
                    "h-2 rounded-full transition-all",
                    variant === "destructive" ? "bg-destructive" : "bg-primary"
                  )}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <p className="text-sm">
                Progress: {taskStatus.progress.current}/{taskStatus.progress.total}
              </p>
            </div>
          )}
          {taskStatus.error && (
            <p className="mt-2 text-destructive">Error: {taskStatus.error}</p>
          )}
          {taskStatus.result && (
            <div className="mt-2">
              <p>{taskStatus.result.message}</p>
              {taskStatus.result.failed_stores &&
                taskStatus.result.failed_stores.length > 0 && (
                  <p className="mt-1 text-destructive">
                    Failed stores: {taskStatus.result.failed_stores.join(", ")}
                  </p>
                )}
            </div>
          )}
        </AlertDescription>
      </Alert>
    );
  }

  if (error) {
    const errorMessage =
      error.response?.status === 401
        ? "Your session has expired. Please refresh the page and try again."
        : error.response?.status === 404
        ? "The requested resource was not found."
        : error.response?.status === 500
        ? "An internal server error occurred. Please try again later."
        : error.message;

    return (
      <Alert variant="destructive" className="mb-4">
        <AlertTitle>Josiah Error!</AlertTitle>
        <AlertDescription>{errorMessage}</AlertDescription>
      </Alert>
    );
  }

  if (isSuccess) {
    return (
      <Alert variant="success" className="mb-4">
        <AlertTitle>Josiah is on it!</AlertTitle>
        <AlertDescription>{successMessage}</AlertDescription>
      </Alert>
    );
  }

  return null;
}
