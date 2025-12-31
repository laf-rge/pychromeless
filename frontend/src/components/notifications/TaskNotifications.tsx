import { useMemo } from "react";
import { useTaskStore } from "../../stores/taskStore";
import { TaskNotificationCard } from "./TaskNotificationCard";

/**
 * Global task notifications component
 * Displays toast-style notifications for active and completed tasks
 * Fixed position at top-right of screen, persists across navigation
 */
export function TaskNotifications() {
  const { activeTasks, completedTasks, failedTasks, visibleNotifications, dismissNotification } =
    useTaskStore();

  // Get tasks that should be visible in notifications
  const visibleTasks = useMemo(() => {
    const tasks = [];
    for (const taskId of visibleNotifications) {
      const task =
        activeTasks.get(taskId) ||
        completedTasks.get(taskId) ||
        failedTasks.get(taskId);
      if (task) {
        tasks.push(task);
      }
    }
    // Sort by updated_at descending (newest first)
    return tasks.sort((a, b) => b.updated_at - a.updated_at);
  }, [activeTasks, completedTasks, failedTasks, visibleNotifications]);

  if (visibleTasks.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md pointer-events-auto">
      {visibleTasks.map((task) => (
        <TaskNotificationCard
          key={task.task_id}
          task={task}
          onDismiss={() => dismissNotification(task.task_id)}
        />
      ))}
    </div>
  );
}
