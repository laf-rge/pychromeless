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

// Track createImmediateTask calls
const mockCreateImmediateTask = mock(() => {});

// Mock taskStore
mock.module('../../../stores/taskStore', () => ({
  useTaskStore: (selector: (state: Record<string, unknown>) => unknown) =>
    selector({
      createImmediateTask: mockCreateImmediateTask,
      completedTasks: new Map(),
      failedTasks: new Map(),
      activeTasks: new Map(),
      visibleNotifications: new Set(),
    }),
}));

// Mock axios - returns 202 with task_id
const mockPost = mock(() =>
  Promise.resolve({
    headers: { 'content-type': 'application/json' },
    data: { task_id: 'fdms-task-123', message: 'Processing started' },
  })
);

mock.module('axios', () => ({
  default: {
    create: () => ({
      post: mockPost,
    }),
  },
}));

// Import after mocks
import { FdmsImport } from '../FdmsImport';
import { renderWithProviders } from '../../../test-utils/test-providers';

describe('FdmsImport', () => {
  beforeAll(() => {
    resetFakeTimerState();
  });

  beforeEach(() => {
    mockPost.mockClear();
    mockCreateImmediateTask.mockClear();
  });

  it('renders the form with file input', () => {
    renderWithProviders(<FdmsImport />);

    expect(screen.getByText('FDMS Statement Import')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /choose files/i })).toBeInTheDocument();
  });

  it('shows error when submitted without files', async () => {
    renderWithProviders(<FdmsImport />);

    const submitButton = screen.getByRole('button', { name: /submit/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/please select at least one/i)).toBeInTheDocument();
    });
  });

  it('submits and calls createImmediateTask on 202 response', async () => {
    renderWithProviders(<FdmsImport />);

    // Select PDF files
    const fileInput = screen.getByLabelText(/select fdms statement/i);
    const testFile = new File(['%PDF-fake'], 'statement.pdf', { type: 'application/pdf' });

    // Use fireEvent for file input since userEvent doesn't support it well
    const { fireEvent } = await import('@testing-library/react');
    fireEvent.change(fileInput, { target: { files: [testFile] } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(mockCreateImmediateTask).toHaveBeenCalledWith(
        'fdms-task-123',
        'fdms_statement_import'
      );
    });
  });
});
