import { vi } from 'vitest';
import type { PublicClientApplication } from '@azure/msal-browser';

// Mock MSAL instance
export const createMockMsalInstance = (): PublicClientApplication => {
  return {
    getActiveAccount: vi.fn(() => ({
      username: 'test@example.com',
      name: 'Test User',
      localAccountId: 'test-account-id',
    })),
    acquireTokenSilent: vi.fn(() =>
      Promise.resolve({
        accessToken: 'mock-access-token',
        expiresOn: new Date(Date.now() + 3600000),
      })
    ),
    acquireTokenPopup: vi.fn(() =>
      Promise.resolve({
        accessToken: 'mock-access-token',
        expiresOn: new Date(Date.now() + 3600000),
      })
    ),
  } as unknown as PublicClientApplication;
};

// Mock WebSocket
export class MockWebSocket {
  static instances: MockWebSocket[] = [];

  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  readyState: number = WebSocket.CONNECTING;

  send = vi.fn();
  close = vi.fn();

  constructor(_url: string) {
    MockWebSocket.instances.push(this);
  }

  triggerOpen() {
    this.readyState = WebSocket.OPEN;
    if (this.onopen) {
      this.onopen();
    }
  }

  triggerMessage(data: unknown) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) } as MessageEvent);
    }
  }

  triggerClose() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({} as CloseEvent);
    }
  }

  static getLastInstance() {
    return this.instances[this.instances.length - 1];
  }

  static reset() {
    this.instances = [];
  }
}

// Mock fetch
export const createMockFetch = (responses: Record<string, unknown> = {}) => {
  return vi.fn((url: string) => {
    const response = responses[url] || { data: [] };
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(response),
      text: () => Promise.resolve(JSON.stringify(response)),
    });
  });
};

// Task factory for tests
export const createMockTask = (overrides = {}) => {
  return {
    task_id: 'test-task-id',
    operation: 'daily_sales',
    operationDisplayName: 'Daily Sales',
    status: 'started',
    created_at: Date.now(),
    updated_at: Date.now(),
    color: 'border-blue-500',
    ...overrides,
  };
};
