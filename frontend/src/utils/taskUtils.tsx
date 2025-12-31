import { ReactNode } from "react";
import { CheckCircle, XCircle, AlertTriangle, Loader2 } from "lucide-react";
import { TaskStatusType } from "../services/TaskStatusService";

/**
 * Color palette for task visual identification
 */
const TASK_COLORS = [
  "#3b82f6", // blue
  "#8b5cf6", // purple
  "#ec4899", // pink
  "#f97316", // orange
  "#10b981", // green
  "#06b6d4", // cyan
  "#f59e0b", // amber
  "#6366f1", // indigo
  "#14b8a6", // teal
  "#f43f5e", // rose
];

/**
 * Generate a deterministic color from a task ID using hash function
 * This ensures the same task ID always gets the same color
 */
export function generateTaskColor(taskId: string): string {
  let hash = 0;
  for (let i = 0; i < taskId.length; i++) {
    hash = taskId.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash; // Convert to 32bit integer
  }

  const index = Math.abs(hash) % TASK_COLORS.length;
  return TASK_COLORS[index];
}

/**
 * Map task status to Alert component variant
 */
export function getStatusVariant(
  status: TaskStatusType
): "default" | "destructive" | "warning" | "success" {
  const variantMap: Record<
    TaskStatusType,
    "default" | "destructive" | "warning" | "success"
  > = {
    started: "default",
    processing: "default",
    completed: "success",
    completed_with_errors: "warning",
    failed: "destructive",
    error: "destructive",
  };
  return variantMap[status] || "default";
}

/**
 * Get icon component for task status
 */
export function getStatusIcon(status: TaskStatusType): ReactNode {
  const iconClass = "h-4 w-4";

  switch (status) {
    case "started":
    case "processing":
      return <Loader2 className={`${iconClass} animate-spin`} />;
    case "completed":
      return <CheckCircle className={`${iconClass} text-green-600`} />;
    case "completed_with_errors":
      return <AlertTriangle className={`${iconClass} text-yellow-600`} />;
    case "failed":
    case "error":
      return <XCircle className={`${iconClass} text-red-600`} />;
    default:
      return null;
  }
}

/**
 * Get badge variant for task status
 * Maps to the same variants as Alert component
 */
export function getStatusBadgeVariant(
  status: TaskStatusType
): "default" | "destructive" | "warning" | "success" {
  return getStatusVariant(status);
}

/**
 * Get human-readable status title
 */
export function getStatusTitle(status: TaskStatusType): string {
  const titleMap: Record<TaskStatusType, string> = {
    started: "Processing Started",
    processing: "Processing in Progress",
    completed: "Processing Complete",
    completed_with_errors: "Processing Complete with Errors",
    failed: "Processing Failed",
    error: "Processing Error",
  };
  return titleMap[status] || status;
}

/**
 * Calculate progress percentage from progress object
 */
export function calculateProgressPercent(progress?: {
  current: number;
  total: number;
}): number {
  if (!progress || progress.total === 0) return 0;
  return Math.round((progress.current / progress.total) * 100);
}

/**
 * Check if task is in a terminal state (completed or failed)
 */
export function isTaskTerminal(status: TaskStatusType): boolean {
  return [
    "completed",
    "completed_with_errors",
    "failed",
    "error",
  ].includes(status);
}

/**
 * Check if task is in a active/running state
 */
export function isTaskActive(status: TaskStatusType): boolean {
  return ["started", "processing"].includes(status);
}

/**
 * Format timestamp to relative time (e.g., "2 minutes ago")
 */
export function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days} day${days > 1 ? "s" : ""} ago`;
  if (hours > 0) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  if (minutes > 0) return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
  if (seconds > 0) return `${seconds} second${seconds > 1 ? "s" : ""} ago`;
  return "just now";
}
