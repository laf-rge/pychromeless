import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useTaskStore } from '../taskStore';
import type { TaskStatus } from '../../services/TaskStatusService';
import { OperationType } from '../../services/WebSocketService';

describe('taskStore', () => {
  beforeEach(() => {
    // Reset store to initial state
    useTaskStore.setState({
      activeTasks: new Map(),
      completedTasks: new Map(),
      failedTasks: new Map(),
      visibleNotifications: new Set(),
      isConnected: false,
      isLoadingHistory: false,
      historyError: null,
      dismissTimers: new Map(),
      msalInstance: null,
    });
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('handleTaskUpdate', () => {
    it('adds new task to activeTasks when status is started', () => {
      const payload: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'task-123',
        operation: OperationType.DAILY_SALES,
        status: 'started',
        progress: { current: 0, total: 4, message: 'Starting...' },
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Daily Sales',
      };

      useTaskStore.getState().handleTaskUpdate(payload);

      const { activeTasks, visibleNotifications } = useTaskStore.getState();
      expect(activeTasks.has('task-123')).toBe(true);
      expect(visibleNotifications.has('task-123')).toBe(true);
    });

    it('moves task from active to completed on completion', () => {
      const startPayload: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'task-123',
        operation: OperationType.DAILY_SALES,
        status: 'started',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Daily Sales',
      };

      useTaskStore.getState().handleTaskUpdate(startPayload);

      const completePayload: TaskStatus & { operationDisplayName?: string } = {
        ...startPayload,
        status: 'completed',
        updated_at: Math.floor(Date.now() / 1000),
        result: { success: true, message: 'All done!' },
      };

      useTaskStore.getState().handleTaskUpdate(completePayload);

      const { activeTasks, completedTasks } = useTaskStore.getState();
      expect(activeTasks.has('task-123')).toBe(false);
      expect(completedTasks.has('task-123')).toBe(true);
    });

    it('schedules auto-dismiss for completed tasks', () => {
      const payload: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'task-123',
        operation: OperationType.DAILY_SALES,
        status: 'completed',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Daily Sales',
      };

      useTaskStore.getState().handleTaskUpdate(payload);

      const { visibleNotifications } = useTaskStore.getState();
      expect(visibleNotifications.has('task-123')).toBe(true);

      // Fast-forward 10 seconds
      vi.advanceTimersByTime(10000);

      const { visibleNotifications: afterDismiss } = useTaskStore.getState();
      expect(afterDismiss.has('task-123')).toBe(false);
    });

    it('moves task to failedTasks when status is failed', () => {
      const payload: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'task-123',
        operation: OperationType.DAILY_SALES,
        status: 'failed',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        error: 'Something went wrong',
        operationDisplayName: 'Daily Sales',
      };

      useTaskStore.getState().handleTaskUpdate(payload);

      const { failedTasks, visibleNotifications } = useTaskStore.getState();
      expect(failedTasks.has('task-123')).toBe(true);
      expect(visibleNotifications.has('task-123')).toBe(true);
    });

    it('respects max active task limit', () => {
      // Add 21 active tasks (max is 20)
      for (let i = 1; i <= 21; i++) {
        const payload: TaskStatus & { operationDisplayName?: string } = {
          task_id: `task-${i}`,
          operation: OperationType.DAILY_SALES,
          status: 'started',
          created_at: Math.floor(Date.now() / 1000) + i,
          updated_at: Math.floor(Date.now() / 1000) + i,
          operationDisplayName: 'Daily Sales',
        };
        useTaskStore.getState().handleTaskUpdate(payload);
      }

      const { activeTasks } = useTaskStore.getState();
      expect(activeTasks.size).toBeLessThanOrEqual(20);
    });

    it('ignores stale updates', () => {
      const newerPayload: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'task-123',
        operation: OperationType.DAILY_SALES,
        status: 'processing',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Daily Sales',
      };

      useTaskStore.getState().handleTaskUpdate(newerPayload);

      const olderPayload: TaskStatus & { operationDisplayName?: string } = {
        ...newerPayload,
        status: 'started',
        updated_at: Math.floor(Date.now() / 1000) - 3600, // 1 hour ago
      };

      useTaskStore.getState().handleTaskUpdate(olderPayload);

      const { activeTasks } = useTaskStore.getState();
      const task = activeTasks.get('task-123');
      expect(task?.status).toBe('processing'); // Should still be processing, not started
    });
  });

  describe('dismissNotification', () => {
    it('removes task from visible notifications', () => {
      const payload: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'task-123',
        operation: OperationType.DAILY_SALES,
        status: 'started',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Daily Sales',
      };

      useTaskStore.getState().handleTaskUpdate(payload);
      useTaskStore.getState().dismissNotification('task-123');

      const { visibleNotifications } = useTaskStore.getState();
      expect(visibleNotifications.has('task-123')).toBe(false);
    });

    it('cancels auto-dismiss timer when manually dismissed', () => {
      const payload: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'task-123',
        operation: OperationType.DAILY_SALES,
        status: 'completed',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Daily Sales',
      };

      useTaskStore.getState().handleTaskUpdate(payload);
      useTaskStore.getState().dismissNotification('task-123');

      // Timer should be cancelled
      vi.advanceTimersByTime(10000);

      const { dismissTimers } = useTaskStore.getState();
      expect(dismissTimers.has('task-123')).toBe(false);
    });
  });

  describe('clearAllNotifications', () => {
    it('removes all visible notifications', () => {
      // Add multiple tasks
      for (let i = 1; i <= 3; i++) {
        const payload: TaskStatus & { operationDisplayName?: string } = {
          task_id: `task-${i}`,
          operation: OperationType.DAILY_SALES,
          status: 'started',
          created_at: Math.floor(Date.now() / 1000),
          updated_at: Math.floor(Date.now() / 1000),
          operationDisplayName: 'Daily Sales',
        };
        useTaskStore.getState().handleTaskUpdate(payload);
      }

      expect(useTaskStore.getState().visibleNotifications.size).toBe(3);

      useTaskStore.getState().clearAllNotifications();

      expect(useTaskStore.getState().visibleNotifications.size).toBe(0);
      expect(useTaskStore.getState().dismissTimers.size).toBe(0);
    });
  });

  describe('setConnectionStatus', () => {
    it('updates connection status', () => {
      useTaskStore.getState().setConnectionStatus(true);
      expect(useTaskStore.getState().isConnected).toBe(true);

      useTaskStore.getState().setConnectionStatus(false);
      expect(useTaskStore.getState().isConnected).toBe(false);
    });
  });

  describe('getAllTasks', () => {
    it('returns all tasks from all maps', () => {
      const activeTask: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'active-1',
        operation: OperationType.DAILY_SALES,
        status: 'processing',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Daily Sales',
      };

      const completedTask: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'completed-1',
        operation: OperationType.INVOICE_SYNC,
        status: 'completed',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Invoice Sync',
      };

      const failedTask: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'failed-1',
        operation: OperationType.EMAIL_TIPS,
        status: 'failed',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Email Tips',
        error: 'Test error',
      };

      useTaskStore.getState().handleTaskUpdate(activeTask);
      useTaskStore.getState().handleTaskUpdate(completedTask);
      useTaskStore.getState().handleTaskUpdate(failedTask);

      const allTasks = useTaskStore.getState().getAllTasks();
      expect(allTasks.length).toBe(3);
    });
  });

  describe('getTasksByOperation', () => {
    it('filters tasks by operation type', () => {
      const task1: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'task-1',
        operation: OperationType.DAILY_SALES,
        status: 'completed',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Daily Sales',
      };

      const task2: TaskStatus & { operationDisplayName?: string } = {
        task_id: 'task-2',
        operation: OperationType.INVOICE_SYNC,
        status: 'completed',
        created_at: Math.floor(Date.now() / 1000),
        updated_at: Math.floor(Date.now() / 1000),
        operationDisplayName: 'Invoice Sync',
      };

      useTaskStore.getState().handleTaskUpdate(task1);
      useTaskStore.getState().handleTaskUpdate(task2);

      const dailySalesTasks = useTaskStore.getState().getTasksByOperation(OperationType.DAILY_SALES);
      expect(dailySalesTasks.length).toBe(1);
      expect(dailySalesTasks[0].task_id).toBe('task-1');
    });
  });
});
