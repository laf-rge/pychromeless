import { mock, jest } from 'bun:test';
import type { PublicClientApplication } from '@azure/msal-browser';

// Mock MSAL instance
export const createMockMsalInstance = (): PublicClientApplication => {
  const mockLogger = {
    error: mock(() => {}),
    warning: mock(() => {}),
    info: mock(() => {}),
    verbose: mock(() => {}),
    trace: mock(() => {}),
    clone: mock(() => {}),
  };

  return {
    getActiveAccount: mock(() => ({
      username: 'test@example.com',
      name: 'Test User',
      localAccountId: 'test-account-id',
      homeAccountId: 'test-home-id',
      environment: 'login.windows.net',
      tenantId: 'test-tenant-id',
    })),
    getAllAccounts: mock(() => []),
    acquireTokenSilent: mock(() =>
      Promise.resolve({
        accessToken: 'mock-access-token',
        expiresOn: new Date(Date.now() + 3600000),
      })
    ),
    acquireTokenPopup: mock(() =>
      Promise.resolve({
        accessToken: 'mock-access-token',
        expiresOn: new Date(Date.now() + 3600000),
      })
    ),
    getLogger: mock(() => mockLogger),
    setLogger: mock(() => {}),
    setActiveAccount: mock(() => {}),
    initialize: mock(() => Promise.resolve()),
    handleRedirectPromise: mock(() => Promise.resolve(null)),
  } as unknown as PublicClientApplication;
};

// Use globalThis to ensure truly shared state across all module instances
// This prevents Bun's module isolation from creating separate instances arrays
const MOCK_WS_REGISTRY_KEY = '__mockWebSocketInstances__';

function getMockWebSocketInstances(): MockWebSocket[] {
  if (!(MOCK_WS_REGISTRY_KEY in globalThis)) {
    (globalThis as Record<string, unknown>)[MOCK_WS_REGISTRY_KEY] = [];
  }
  return (globalThis as Record<string, unknown>)[MOCK_WS_REGISTRY_KEY] as MockWebSocket[];
}

// Mock WebSocket
export class MockWebSocket {
  // Use globalThis registry to avoid module identity issues
  static get instances(): MockWebSocket[] {
    return getMockWebSocketInstances();
  }

  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  readyState: number = WebSocket.CONNECTING;

  send = mock(() => {});
  close = mock(() => {});

  constructor(_url: string) {
    getMockWebSocketInstances().push(this);
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

  static getLastInstance(): MockWebSocket {
    const instances = getMockWebSocketInstances();
    return instances[instances.length - 1];
  }

  static reset() {
    (globalThis as Record<string, unknown>)[MOCK_WS_REGISTRY_KEY] = [];
  }
}

// Mock fetch
export const createMockFetch = (responses: Record<string, unknown> = {}) => {
  return mock((url: string) => {
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

/**
 * Reset fake timer state to prevent testing-library "Fake timers are not active" errors.
 *
 * Bun's jest.useRealTimers() sets setTimeout.clock = false instead of deleting it,
 * but @testing-library/dom checks hasOwnProperty('clock') which returns true for any value.
 * This causes testing-library to think fake timers are enabled when they're not.
 *
 * Call this in beforeAll() for test files that use testing-library's async utilities
 * (waitFor, userEvent, etc.) when other test files in the suite use fake timers.
 */
export function resetFakeTimerState(): void {
  jest.useRealTimers();
  if (Object.prototype.hasOwnProperty.call(globalThis.setTimeout, 'clock')) {
    delete (globalThis.setTimeout as unknown as { clock?: unknown }).clock;
  }
  if (Object.prototype.hasOwnProperty.call(globalThis.setTimeout, '_isMockFunction')) {
    delete (globalThis.setTimeout as unknown as { _isMockFunction?: unknown })._isMockFunction;
  }
}
