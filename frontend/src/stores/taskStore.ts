import { create } from "zustand";
import {
  TaskStatus,
  TaskStatusType,
} from "../services/TaskStatusService";
import TaskStatusService from "../services/TaskStatusService";
import { OperationType, OperationDisplayNames } from "../services/WebSocketService";
import { generateTaskColor } from "../utils/taskUtils";
import { logger } from "../utils/logger";
import type { IPublicClientApplication } from "@azure/msal-browser";

/**
 * Enhanced task information with display properties
 */
export interface TaskInfo extends TaskStatus {
  operationDisplayName: string;
  color: string; // Visual identifier for this task
}

/**
 * Task store state
 */
interface TaskState {
  // Active tasks currently running
  activeTasks: Map<string, TaskInfo>;

  // Completed tasks (auto-dismissed from notifications but kept for history)
  completedTasks: Map<string, TaskInfo>;

  // Failed tasks
  failedTasks: Map<string, TaskInfo>;

  // Notification visibility (tasks shown in toast notifications)
  visibleNotifications: Set<string>;

  // WebSocket connection status
  isConnected: boolean;

  // Loading state for history fetch
  isLoadingHistory: boolean;

  // Error state for history fetch
  historyError: string | null;

  // Auto-dismiss timers
  dismissTimers: Map<string, number>;

  // MSAL instance for API calls
  msalInstance: IPublicClientApplication | null;
}

/**
 * Task store actions
 */
interface TaskActions {
  // Initialization
  setMsalInstance: (instance: IPublicClientApplication) => void;

  // WebSocket message handler
  handleTaskUpdate: (payload: TaskStatus & { operationDisplayName?: string }) => void;

  // Create immediate task from API response (for async operations)
  createImmediateTask: (taskId: string, operation: OperationType) => void;

  // Notification management
  dismissNotification: (taskId: string) => void;
  clearAllNotifications: () => void;

  // History management
  loadTaskHistory: () => Promise<void>;
  clearHistory: () => void;

  // Connection status
  setConnectionStatus: (connected: boolean) => void;

  // Task filtering for Dashboard
  getTasksByOperation: (operation: OperationType) => TaskInfo[];
  getTasksByStatus: (status: TaskStatusType) => TaskInfo[];
  getTasksByDateRange: (start: Date, end: Date) => TaskInfo[];
  getAllTasks: () => TaskInfo[];

  // Internal helper
  scheduleAutoDismiss: (taskId: string) => void;
  cancelAutoDismiss: (taskId: string) => void;
}

type TaskStore = TaskState & TaskActions;

/**
 * Maximum number of tasks to keep in each category
 */
const MAX_ACTIVE_TASKS = 20;
const MAX_COMPLETED_TASKS = 100;
const MAX_FAILED_TASKS = 50;

/**
 * Auto-dismiss delay in milliseconds (10 seconds)
 */
const AUTO_DISMISS_DELAY = 10000;

/**
 * Create the task store
 */
export const useTaskStore = create<TaskStore>((set, get) => ({
  // Initial state
  activeTasks: new Map(),
  completedTasks: new Map(),
  failedTasks: new Map(),
  visibleNotifications: new Set(),
  isConnected: false,
  isLoadingHistory: false,
  historyError: null,
  dismissTimers: new Map(),
  msalInstance: null,

  // Set MSAL instance for API calls
  setMsalInstance: (instance: IPublicClientApplication) => {
    set({ msalInstance: instance });
  },

  // Handle incoming WebSocket messages
  handleTaskUpdate: (payload) => {
    const taskId = payload.task_id;
    const status = payload.status;

    // Create enriched task info
    // Convert timestamps from seconds (backend) to milliseconds (JavaScript standard)
    const taskInfo: TaskInfo = {
      ...payload,
      created_at: payload.created_at * 1000,
      updated_at: payload.updated_at * 1000,
      operationDisplayName:
        payload.operationDisplayName ||
        OperationDisplayNames[payload.operation] ||
        payload.operation,
      color: generateTaskColor(taskId),
    };

    logger.debug(`Task update received: ${taskId} - ${status}`, taskInfo);

    set((state) => {
      // Clone maps and sets for immutability
      const activeTasks = new Map(state.activeTasks);
      const completedTasks = new Map(state.completedTasks);
      const failedTasks = new Map(state.failedTasks);
      const visibleNotifications = new Set(state.visibleNotifications);

      // Only update if this is newer than existing data
      const existing =
        activeTasks.get(taskId) ||
        completedTasks.get(taskId) ||
        failedTasks.get(taskId);

      if (existing && existing.updated_at > taskInfo.updated_at) {
        logger.debug(`Ignoring stale update for task ${taskId}`);
        return state; // Don't update with stale data
      }

      // Remove from all maps first
      activeTasks.delete(taskId);
      completedTasks.delete(taskId);
      failedTasks.delete(taskId);

      // Route to appropriate map based on status
      if (status === "completed" || status === "completed_with_errors") {
        completedTasks.set(taskId, taskInfo);
        visibleNotifications.add(taskId); // Show completion notification

        // Limit completed tasks
        if (completedTasks.size > MAX_COMPLETED_TASKS) {
          // Remove oldest task
          const oldestTaskId = Array.from(completedTasks.entries()).sort(
            (a, b) => a[1].updated_at - b[1].updated_at
          )[0]?.[0];
          if (oldestTaskId) {
            completedTasks.delete(oldestTaskId);
            visibleNotifications.delete(oldestTaskId);
          }
        }

        // Schedule auto-dismiss for completed tasks
        get().scheduleAutoDismiss(taskId);
      } else if (status === "failed" || status === "error") {
        failedTasks.set(taskId, taskInfo);
        visibleNotifications.add(taskId); // Show failure notification

        // Limit failed tasks
        if (failedTasks.size > MAX_FAILED_TASKS) {
          const oldestTaskId = Array.from(failedTasks.entries()).sort(
            (a, b) => a[1].updated_at - b[1].updated_at
          )[0]?.[0];
          if (oldestTaskId) {
            failedTasks.delete(oldestTaskId);
            visibleNotifications.delete(oldestTaskId);
          }
        }

        // Failed tasks stay visible until manually dismissed
      } else {
        // started, processing
        activeTasks.set(taskId, taskInfo);
        visibleNotifications.add(taskId);

        // Limit active tasks
        if (activeTasks.size > MAX_ACTIVE_TASKS) {
          const oldestTaskId = Array.from(activeTasks.entries()).sort(
            (a, b) => a[1].updated_at - b[1].updated_at
          )[0]?.[0];
          if (oldestTaskId) {
            activeTasks.delete(oldestTaskId);
            visibleNotifications.delete(oldestTaskId);
          }
        }
      }

      return {
        activeTasks,
        completedTasks,
        failedTasks,
        visibleNotifications,
      };
    });
  },

  // Create an immediate task entry when API returns task_id (for async operations)
  // This ensures the notification appears immediately without waiting for WebSocket
  createImmediateTask: (taskId: string, operation: OperationType) => {
    const now = Date.now();
    const taskInfo: TaskInfo = {
      task_id: taskId,
      operation,
      status: "started",
      created_at: now,
      updated_at: now,
      operationDisplayName: OperationDisplayNames[operation] || operation,
      color: generateTaskColor(taskId),
    };

    logger.debug(`Creating immediate task: ${taskId} - ${operation}`, taskInfo);

    set((state) => {
      // Don't overwrite if task already exists (WebSocket may have been faster)
      if (
        state.activeTasks.has(taskId) ||
        state.completedTasks.has(taskId) ||
        state.failedTasks.has(taskId)
      ) {
        logger.debug(`Task ${taskId} already exists, skipping immediate create`);
        return state;
      }

      const activeTasks = new Map(state.activeTasks);
      const visibleNotifications = new Set(state.visibleNotifications);

      activeTasks.set(taskId, taskInfo);
      visibleNotifications.add(taskId);

      return { activeTasks, visibleNotifications };
    });
  },

  // Dismiss a notification (remove from visible notifications)
  dismissNotification: (taskId: string) => {
    set((state) => {
      const visibleNotifications = new Set(state.visibleNotifications);
      visibleNotifications.delete(taskId);

      // Cancel auto-dismiss timer if exists
      get().cancelAutoDismiss(taskId);

      return { visibleNotifications };
    });
  },

  // Clear all notifications
  clearAllNotifications: () => {
    // Cancel all auto-dismiss timers
    get().dismissTimers.forEach((timerId) => {
      window.clearTimeout(timerId);
    });

    set({
      visibleNotifications: new Set(),
      dismissTimers: new Map(),
    });
  },

  // Load task history from backend
  loadTaskHistory: async () => {
    const { msalInstance } = get();
    if (!msalInstance) {
      logger.error("Cannot load task history: MSAL instance not set");
      set({ historyError: "Authentication not initialized" });
      return;
    }

    // Check if user is authenticated
    const activeAccount = msalInstance.getActiveAccount();
    if (!activeAccount) {
      logger.debug("No active account, skipping task history load");
      set({ historyError: null }); // Clear error, user just not logged in yet
      return;
    }

    set({ isLoadingHistory: true, historyError: null });

    try {
      const taskService = TaskStatusService.getInstance(msalInstance);
      const tasks = await taskService.getRecentTasks(24, 100);

      logger.debug(`Loaded ${tasks.length} tasks from history`);

      // Process each task
      tasks.forEach((task: TaskStatus) => {
        // Convert timestamps from seconds (backend) to milliseconds (JavaScript standard)
        const taskInfo: TaskInfo = {
          ...task,
          created_at: task.created_at * 1000,
          updated_at: task.updated_at * 1000,
          operationDisplayName:
            OperationDisplayNames[task.operation] || String(task.operation),
          color: generateTaskColor(task.task_id),
        };

        set((state) => {
          const activeTasks = new Map(state.activeTasks);
          const completedTasks = new Map(state.completedTasks);
          const failedTasks = new Map(state.failedTasks);

          // Check if we already have a newer version of this task
          const existing =
            activeTasks.get(task.task_id) ||
            completedTasks.get(task.task_id) ||
            failedTasks.get(task.task_id);

          if (existing && existing.updated_at > taskInfo.updated_at) {
            // Skip this older record
            return state;
          }

          // Remove from all maps first (prevents duplicates)
          activeTasks.delete(task.task_id);
          completedTasks.delete(task.task_id);
          failedTasks.delete(task.task_id);

          // Route based on status
          if (
            task.status === "completed" ||
            task.status === "completed_with_errors"
          ) {
            completedTasks.set(task.task_id, taskInfo);
          } else if (task.status === "failed" || task.status === "error") {
            failedTasks.set(task.task_id, taskInfo);
          } else {
            activeTasks.set(task.task_id, taskInfo);
          }

          return { activeTasks, completedTasks, failedTasks };
        });
      });
    } catch (error) {
      logger.error("Failed to load task history:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to load task history";
      set({ historyError: errorMessage });
    } finally {
      set({ isLoadingHistory: false });
    }
  },

  // Clear all task history
  clearHistory: () => {
    // Cancel all timers
    get().dismissTimers.forEach((timerId) => {
      window.clearTimeout(timerId);
    });

    set({
      activeTasks: new Map(),
      completedTasks: new Map(),
      failedTasks: new Map(),
      visibleNotifications: new Set(),
      dismissTimers: new Map(),
    });
  },

  // Update WebSocket connection status
  setConnectionStatus: (connected: boolean) => {
    set({ isConnected: connected });
    logger.debug(`WebSocket connection status: ${connected ? "connected" : "disconnected"}`);
  },

  // Get tasks by operation type
  getTasksByOperation: (operation: OperationType) => {
    const { activeTasks, completedTasks, failedTasks } = get();
    const allTasks = [
      ...Array.from(activeTasks.values()),
      ...Array.from(completedTasks.values()),
      ...Array.from(failedTasks.values()),
    ];
    return allTasks.filter((task) => task.operation === operation);
  },

  // Get tasks by status
  getTasksByStatus: (status: TaskStatusType) => {
    const { activeTasks, completedTasks, failedTasks } = get();
    const allTasks = [
      ...Array.from(activeTasks.values()),
      ...Array.from(completedTasks.values()),
      ...Array.from(failedTasks.values()),
    ];
    return allTasks.filter((task) => task.status === status);
  },

  // Get tasks by date range
  getTasksByDateRange: (start: Date, end: Date) => {
    const { activeTasks, completedTasks, failedTasks } = get();
    const allTasks = [
      ...Array.from(activeTasks.values()),
      ...Array.from(completedTasks.values()),
      ...Array.from(failedTasks.values()),
    ];
    const startTime = start.getTime();
    const endTime = end.getTime();
    return allTasks.filter(
      (task) => task.updated_at >= startTime && task.updated_at <= endTime
    );
  },

  // Get all tasks
  getAllTasks: () => {
    const { activeTasks, completedTasks, failedTasks } = get();
    return [
      ...Array.from(activeTasks.values()),
      ...Array.from(completedTasks.values()),
      ...Array.from(failedTasks.values()),
    ];
  },

  // Schedule auto-dismiss for a task
  scheduleAutoDismiss: (taskId: string) => {
    // Cancel existing timer if any
    get().cancelAutoDismiss(taskId);

    // Set new timer
    const timerId = window.setTimeout(() => {
      get().dismissNotification(taskId);
    }, AUTO_DISMISS_DELAY);

    set((state) => {
      const dismissTimers = new Map(state.dismissTimers);
      dismissTimers.set(taskId, timerId);
      return { dismissTimers };
    });

    logger.debug(`Auto-dismiss scheduled for task ${taskId} in ${AUTO_DISMISS_DELAY}ms`);
  },

  // Cancel auto-dismiss for a task
  cancelAutoDismiss: (taskId: string) => {
    const { dismissTimers } = get();
    const timerId = dismissTimers.get(taskId);

    if (timerId) {
      window.clearTimeout(timerId);
      set((state) => {
        const newTimers = new Map(state.dismissTimers);
        newTimers.delete(taskId);
        return { dismissTimers: newTimers };
      });
      logger.debug(`Auto-dismiss cancelled for task ${taskId}`);
    }
  },
}));
