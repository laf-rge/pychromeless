import type { TaskInfo } from "../stores/taskStore";
import type { Mock } from "vitest";
import { OperationType } from "../services/WebSocketService";

/**
 * Task Store Mock Utilities
 *
 * Due to vitest's hoisting behavior, mocks need to be defined with vi.hoisted()
 * in test files. This file provides types and helper functions.
 *
 * Usage pattern in test files:
 *
 * ```typescript
 * import { vi } from 'vitest';
 *
 * // Use vi.hoisted to define mocks before module loading
 * const { mockCreateImmediateTask, mockCompletedTasks, mockFailedTasks, mockTaskStoreState } =
 *   vi.hoisted(() => {
 *     const mockCreateImmediateTask = vi.fn();
 *     const mockCompletedTasks = new Map();
 *     const mockFailedTasks = new Map();
 *     const mockTaskStoreState = {
 *       createImmediateTask: mockCreateImmediateTask,
 *       completedTasks: mockCompletedTasks,
 *       failedTasks: mockFailedTasks,
 *     };
 *     return { mockCreateImmediateTask, mockCompletedTasks, mockFailedTasks, mockTaskStoreState };
 *   });
 *
 * vi.mock('../../../stores/taskStore', () => ({
 *   useTaskStore: (selector: (state: typeof mockTaskStoreState) => unknown) => {
 *     return selector(mockTaskStoreState);
 *   },
 * }));
 *
 * beforeEach(() => {
 *   vi.clearAllMocks();
 *   mockCompletedTasks.clear();
 *   mockFailedTasks.clear();
 * });
 * ```
 */

// Type for the minimal mock state needed for most tests
export interface MockTaskStoreState {
  createImmediateTask: Mock;
  completedTasks: Map<string, TaskInfo>;
  failedTasks: Map<string, TaskInfo>;
  activeTasks?: Map<string, TaskInfo>;
  visibleNotifications?: Set<string>;
  isConnected?: boolean;
  dismissNotification?: Mock;
  clearAllNotifications?: Mock;
  loadTaskHistory?: Mock;
  setConnectionStatus?: Mock;
}

// Mock task data factory - can be imported and used in tests
export function createMockTaskInfo(overrides: Partial<TaskInfo> = {}): TaskInfo {
  return {
    task_id: "test-task-123",
    operation: OperationType.DAILY_SALES,
    status: "started",
    created_at: Date.now(),
    updated_at: Date.now(),
    operationDisplayName: "Daily Sales Processing",
    color: "#3B82F6",
    ...overrides,
  };
}
