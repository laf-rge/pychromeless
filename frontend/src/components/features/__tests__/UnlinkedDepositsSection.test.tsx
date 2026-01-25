import { describe, it, expect, beforeEach, beforeAll, mock } from 'bun:test';
import { resetFakeTimerState } from '../../../test-utils/test-helpers';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { mockMsalInstance, mockAccount } from '../../../test-utils/MockMsalProvider';

// Mock @azure/msal-react
mock.module('@azure/msal-react', () => ({
  useMsal: () => ({
    instance: mockMsalInstance,
    accounts: [mockAccount],
    inProgress: 'none',
  }),
  MsalProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Define taskStore mock values at module level (replaces vi.hoisted)
const mockCreateImmediateTask = mock(() => {});
const mockCompletedTasks = new Map();
const mockFailedTasks = new Map();
const mockTaskStoreState = {
  createImmediateTask: mockCreateImmediateTask,
  completedTasks: mockCompletedTasks,
  failedTasks: mockFailedTasks,
};

// Mock taskStore
mock.module('../../../stores/taskStore', () => ({
  useTaskStore: (selector: (state: typeof mockTaskStoreState) => unknown) => {
    return selector(mockTaskStoreState);
  },
}));

// Create mock axios response data
const mockDepositsResponse = {
  deposits: [
    {
      id: '1234',
      store: '20358',
      date: '2025-01-15',
      amount: '100.50',
      doc_number: 'DS-20358-20250115',
      qb_url: 'https://app.qbo.intuit.com/app/salesreceipt?txnId=1234',
      has_cents: true,
    },
    {
      id: '5678',
      store: '20367',
      date: '2025-01-16',
      amount: '200.00',
      doc_number: 'DS-20367-20250116',
      qb_url: 'https://app.qbo.intuit.com/app/salesreceipt?txnId=5678',
      has_cents: false,
    },
  ],
  summary: {
    count: 2,
    total_amount: '300.50',
  },
};

const mockEmptyResponse = {
  deposits: [],
  summary: {
    count: 0,
    total_amount: '0.00',
  },
};

// Create mock axios
const mockGet = mock(() => Promise.resolve({ data: mockDepositsResponse }));
const mockPost = mock(() => Promise.resolve({ data: { task_id: 'test-task-123' } }));

mock.module('axios', () => ({
  default: {
    create: () => ({
      get: mockGet,
      post: mockPost,
    }),
  },
}));

// Import component after mocks are set up
import { UnlinkedDepositsSection } from '../UnlinkedDepositsSection';
import { renderWithProviders } from '../../../test-utils/test-providers';

describe('UnlinkedDepositsSection', () => {
  // Prevent testing-library "Fake timers are not active" errors from other test files
  beforeAll(() => {
    resetFakeTimerState();
  });

  beforeEach(() => {
    mockGet.mockClear();
    mockPost.mockClear();
    mockCreateImmediateTask.mockClear();
    mockGet.mockImplementation(() => Promise.resolve({ data: mockDepositsResponse }));
    mockPost.mockImplementation(() => Promise.resolve({ data: { task_id: 'test-task-123' } }));
    mockCompletedTasks.clear();
    mockFailedTasks.clear();
  });

  it('renders the section title and description', async () => {
    renderWithProviders(<UnlinkedDepositsSection />);

    expect(screen.getByText('Unlinked Deposits')).toBeInTheDocument();
    expect(
      screen.getByText(/Sales receipts in QuickBooks without linked bank deposits/)
    ).toBeInTheDocument();
  });

  it('displays loading state initially', async () => {
    // Create a pending promise to keep the loading state
    mockGet.mockImplementation(() => new Promise(() => {}));

    renderWithProviders(<UnlinkedDepositsSection />);

    // Should show at least one spinner during loading
    const spinners = screen.getAllByRole('status');
    expect(spinners.length).toBeGreaterThan(0);
  });

  it('displays deposits in table after loading', async () => {
    renderWithProviders(<UnlinkedDepositsSection />);

    await waitFor(() => {
      expect(screen.getByText('20358')).toBeInTheDocument();
      expect(screen.getByText('20367')).toBeInTheDocument();
    });

    // Check amounts are formatted as currency
    expect(screen.getByText('$100.50')).toBeInTheDocument();
    expect(screen.getByText('$200.00')).toBeInTheDocument();
  });

  it('displays summary with count and total', async () => {
    renderWithProviders(<UnlinkedDepositsSection />);

    await waitFor(() => {
      // Check for the count in the summary - count is in a <strong> tag
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText(/unlinked deposits/)).toBeInTheDocument();
      expect(screen.getByText('$300.50')).toBeInTheDocument();
    });
  });

  it('shows warning badge for amounts with cents', async () => {
    renderWithProviders(<UnlinkedDepositsSection />);

    await waitFor(() => {
      // The deposit with has_cents: true should have a warning badge
      const badges = screen.getAllByTitle(/Amount has cents/);
      expect(badges.length).toBeGreaterThan(0);
    });
  });

  it('shows View in QB links', async () => {
    renderWithProviders(<UnlinkedDepositsSection />);

    await waitFor(() => {
      const viewLinks = screen.getAllByText('View in QB');
      expect(viewLinks.length).toBe(2);
      // Check first link has correct href
      expect(viewLinks[0].closest('a')).toHaveAttribute(
        'href',
        'https://app.qbo.intuit.com/app/salesreceipt?txnId=1234'
      );
    });
  });

  it('shows Re-run button only for items with cents', async () => {
    renderWithProviders(<UnlinkedDepositsSection />);

    await waitFor(() => {
      // Should only show Re-run for the deposit with has_cents: true
      const rerunButtons = screen.getAllByRole('button', { name: 'Re-run' });
      expect(rerunButtons.length).toBe(1);
    });
  });

  it('displays empty state when no deposits', async () => {
    mockGet.mockImplementation(() => Promise.resolve({ data: mockEmptyResponse }));

    renderWithProviders(<UnlinkedDepositsSection />);

    await waitFor(() => {
      expect(
        screen.getByText(/No unlinked deposits found/)
      ).toBeInTheDocument();
    });
  });

  it('displays error state on fetch failure', async () => {
    mockGet.mockImplementation(() => Promise.reject(new Error('Network error')));

    renderWithProviders(<UnlinkedDepositsSection />);

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to fetch unlinked deposits/)
      ).toBeInTheDocument();
    });
  });

  it('refresh button triggers data reload', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UnlinkedDepositsSection />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('20358')).toBeInTheDocument();
    });

    // Clear mock and set up for second call
    mockGet.mockClear();
    mockGet.mockImplementation(() => Promise.resolve({ data: mockEmptyResponse }));

    // Click refresh
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    await user.click(refreshButton);

    // Should call get again
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalled();
    });
  });

  it('re-run button triggers daily sales for specific store', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UnlinkedDepositsSection />);

    // Wait for deposits to load
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Re-run' })).toBeInTheDocument();
    });

    // Click Re-run button
    const rerunButton = screen.getByRole('button', { name: 'Re-run' });
    await user.click(rerunButton);

    // Should call POST to daily_sales endpoint with query params
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalled();
      const postCall = mockPost.mock.calls[0];
      // Check the endpoint URL contains query parameters
      const url = postCall[0] as string;
      expect(url).toContain('year=2025');
      expect(url).toContain('month=01');
      expect(url).toContain('day=15');
      expect(url).toContain('store=20358');
      // Body should be empty string (params are in URL)
      expect(postCall[1]).toBe('');
    });

    // Should create immediate task for notification
    await waitFor(() => {
      expect(mockCreateImmediateTask).toHaveBeenCalledWith('test-task-123', 'daily_sales');
    });
  });
});
