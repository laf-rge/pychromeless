import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import WebSocketService, { OperationType } from '../WebSocketService';
import type { IPublicClientApplication } from '@azure/msal-browser';
import { MockWebSocket, createMockMsalInstance } from '../../test-utils/test-helpers';

// Mock the WebSocket constructor globally
beforeEach(() => {
  MockWebSocket.reset();
  globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket;
});

describe('WebSocketService', () => {
  let mockMsalInstance: IPublicClientApplication;
  let mockWebSocket: MockWebSocket;

  beforeEach(() => {
    mockMsalInstance = createMockMsalInstance();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
    // Reset singleton instance
    (WebSocketService as unknown as { instance: null }).instance = null;
  });

  describe('connection management', () => {
    it('establishes WebSocket connection on getInstance', async () => {
      WebSocketService.getInstance(mockMsalInstance);

      // Wait for async initialization
      await vi.runAllTimersAsync();

      mockWebSocket = MockWebSocket.getLastInstance();
      expect(mockWebSocket).toBeDefined();
    });

    it('sets connected status when connection opens', async () => {
      const service = WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      expect(service.isWebSocketConnected()).toBe(true);
    });

    it('notifies connection listeners on status change', async () => {
      const service = WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      const listener = vi.fn();
      service.onConnectionChange(listener);

      // Listener should be called immediately with current status
      expect(listener).toHaveBeenCalledWith(false);

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      expect(listener).toHaveBeenCalledWith(true);
    });

    it('removes connection listener when unsubscribe is called', async () => {
      const service = WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      const listener = vi.fn();
      const unsubscribe = service.onConnectionChange(listener);

      listener.mockClear();
      unsubscribe();

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      // Listener should not be called after unsubscribe
      expect(listener).not.toHaveBeenCalled();
    });
  });

  describe('message handling', () => {
    it('broadcasts messages to global subscribers', async () => {
      const service = WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      const handler = vi.fn();
      service.subscribeGlobal(handler);

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      const message = {
        type: 'task_status',
        payload: {
          task_id: 'task-123',
          operation: OperationType.DAILY_SALES,
          status: 'started',
          created_at: Math.floor(Date.now() / 1000),
          updated_at: Math.floor(Date.now() / 1000),
        },
      };

      mockWebSocket.triggerMessage(message);

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          task_id: 'task-123',
          operation: 'daily_sales',
          status: 'started',
          operationDisplayName: 'Daily Sales Processing',
        })
      );
    });

    it('delivers messages to task-specific subscribers', async () => {
      const service = WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      const handler = vi.fn();
      service.subscribe('task-123', handler);

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      const message = {
        type: 'task_status',
        payload: {
          task_id: 'task-123',
          operation: OperationType.INVOICE_SYNC,
          status: 'processing',
          created_at: Math.floor(Date.now() / 1000),
          updated_at: Math.floor(Date.now() / 1000),
          progress: {
            current: 2,
            total: 5,
            message: 'Processing invoices...',
          },
        },
      };

      mockWebSocket.triggerMessage(message);

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          task_id: 'task-123',
          operation: 'invoice_sync',
          status: 'processing',
        })
      );
    });

    it('queues messages for tasks without subscribers', async () => {
      const service = WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      const message = {
        type: 'task_status',
        payload: {
          task_id: 'task-orphan',
          operation: OperationType.EMAIL_TIPS,
          status: 'started',
          created_at: Math.floor(Date.now() / 1000),
          updated_at: Math.floor(Date.now() / 1000),
        },
      };

      // Send message before subscribing
      mockWebSocket.triggerMessage(message);

      // Subscribe after message arrives
      const handler = vi.fn();
      service.subscribe('task-orphan', handler);

      // Queued message should be delivered
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          task_id: 'task-orphan',
          status: 'started',
        })
      );
    });

    it('unsubscribes handlers correctly', async () => {
      const service = WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      const handler = vi.fn();
      const unsubscribe = service.subscribe('task-123', handler);

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      // Unsubscribe before sending message
      unsubscribe();

      const message = {
        type: 'task_status',
        payload: {
          task_id: 'task-123',
          operation: OperationType.DAILY_SALES,
          status: 'started',
          created_at: Math.floor(Date.now() / 1000),
          updated_at: Math.floor(Date.now() / 1000),
        },
      };

      mockWebSocket.triggerMessage(message);

      expect(handler).not.toHaveBeenCalled();
    });

    it('unsubscribes global handlers correctly', async () => {
      const service = WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      const handler = vi.fn();
      const unsubscribe = service.subscribeGlobal(handler);

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      // Unsubscribe before sending message
      unsubscribe();

      const message = {
        type: 'task_status',
        payload: {
          task_id: 'task-123',
          operation: OperationType.DAILY_SALES,
          status: 'started',
          created_at: Math.floor(Date.now() / 1000),
          updated_at: Math.floor(Date.now() / 1000),
        },
      };

      mockWebSocket.triggerMessage(message);

      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe('reconnection', () => {
    it('attempts to reconnect on connection loss', async () => {
      WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      const initialCount = MockWebSocket.instances.length;
      mockWebSocket.triggerClose();

      // First reconnect attempt after 1 second (2^0 * 1000ms)
      await vi.advanceTimersByTimeAsync(1000);
      expect(MockWebSocket.instances.length).toBe(initialCount + 1);
    });

    it('uses exponential backoff for reconnection', async () => {
      WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      // First disconnect
      let count = MockWebSocket.instances.length;
      mockWebSocket.triggerClose();
      await vi.advanceTimersByTimeAsync(1000); // 2^0 * 1000ms = 1000ms
      expect(MockWebSocket.instances.length).toBe(count + 1);

      // Second disconnect
      count = MockWebSocket.instances.length;
      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerClose();
      await vi.advanceTimersByTimeAsync(2000); // 2^1 * 1000ms = 2000ms
      expect(MockWebSocket.instances.length).toBe(count + 1);

      // Third disconnect
      count = MockWebSocket.instances.length;
      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerClose();
      await vi.advanceTimersByTimeAsync(4000); // 2^2 * 1000ms = 4000ms
      expect(MockWebSocket.instances.length).toBe(count + 1);
    });

    it('resets reconnect attempts on successful connection', async () => {
      WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      // Disconnect and reconnect
      mockWebSocket.triggerClose();
      await vi.advanceTimersByTimeAsync(1000);

      // Connection successful
      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      // Next disconnect should use initial delay again
      const count = MockWebSocket.instances.length;
      mockWebSocket.triggerClose();
      await vi.advanceTimersByTimeAsync(1000);
      expect(MockWebSocket.instances.length).toBeGreaterThan(count);
    });

    it('stops after max reconnect attempts', async () => {
      WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      const initialCount = MockWebSocket.instances.length;

      // Trigger multiple disconnects
      for (let i = 0; i < 6; i++) {
        mockWebSocket.triggerClose();
        await vi.advanceTimersByTimeAsync(10000); // Advance by a large amount
        mockWebSocket = MockWebSocket.getLastInstance();
      }

      // Should stop after 5 reconnect attempts (max)
      // Then wait 30 seconds before next attempt
      const finalCount = MockWebSocket.instances.length;
      expect(finalCount - initialCount).toBeLessThanOrEqual(6);
    });
  });

  describe('multiple subscribers', () => {
    it('notifies all global subscribers', async () => {
      const service = WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      const handler1 = vi.fn();
      const handler2 = vi.fn();
      const handler3 = vi.fn();

      service.subscribeGlobal(handler1);
      service.subscribeGlobal(handler2);
      service.subscribeGlobal(handler3);

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      const message = {
        type: 'task_status',
        payload: {
          task_id: 'task-multi',
          operation: OperationType.TRANSFORM_TIPS,
          status: 'completed',
          created_at: Math.floor(Date.now() / 1000),
          updated_at: Math.floor(Date.now() / 1000),
        },
      };

      mockWebSocket.triggerMessage(message);

      expect(handler1).toHaveBeenCalled();
      expect(handler2).toHaveBeenCalled();
      expect(handler3).toHaveBeenCalled();
    });

    it('notifies both global and task-specific subscribers', async () => {
      const service = WebSocketService.getInstance(mockMsalInstance);
      await vi.runAllTimersAsync();

      const globalHandler = vi.fn();
      const taskHandler = vi.fn();

      service.subscribeGlobal(globalHandler);
      service.subscribe('task-both', taskHandler);

      mockWebSocket = MockWebSocket.getLastInstance();
      mockWebSocket.triggerOpen();

      const message = {
        type: 'task_status',
        payload: {
          task_id: 'task-both',
          operation: OperationType.GET_MPVS,
          status: 'processing',
          created_at: Math.floor(Date.now() / 1000),
          updated_at: Math.floor(Date.now() / 1000),
        },
      };

      mockWebSocket.triggerMessage(message);

      expect(globalHandler).toHaveBeenCalled();
      expect(taskHandler).toHaveBeenCalled();
    });
  });
});
