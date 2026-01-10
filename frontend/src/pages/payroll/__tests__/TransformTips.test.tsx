import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TransformTips } from '../TransformTips';
import { renderWithProviders } from '../../../test-utils/test-providers';
import { mockMsalInstance, mockAccount } from '../../../test-utils/MockMsalProvider';

// Mock @azure/msal-react
vi.mock('@azure/msal-react', () => ({
  useMsal: () => ({
    instance: mockMsalInstance,
    accounts: [mockAccount],
    inProgress: 'none',
  }),
  MsalProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: () => ({
      post: vi.fn().mockResolvedValue({
        headers: { 'content-type': 'application/json' },
        data: { success: true },
      }),
    }),
  },
}));

describe('TransformTips', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the form with file input', () => {
    renderWithProviders(<TransformTips />);

    expect(screen.getByText('Gusto Tips Transform')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /choose file/i })).toBeInTheDocument();
    expect(screen.getByText('No file selected')).toBeInTheDocument();
  });

  it('shows error when form is submitted without selecting a file', async () => {
    renderWithProviders(<TransformTips />);

    const submitButton = screen.getByRole('button', { name: /submit/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Please select a file')).toBeInTheDocument();
    });
  });

  it('displays filename when a file is selected', async () => {
    renderWithProviders(<TransformTips />);

    // Initially shows "No file selected"
    expect(screen.getByText('No file selected')).toBeInTheDocument();

    // Select a file via the hidden input
    const fileInput = screen.getByLabelText(/select file/i);
    const testFile = new File(['test content'], 'test-report.csv', { type: 'text/csv' });

    fireEvent.change(fileInput, { target: { files: [testFile] } });

    // Should now show the filename
    await waitFor(() => {
      expect(screen.getByText('test-report.csv')).toBeInTheDocument();
      expect(screen.queryByText('No file selected')).not.toBeInTheDocument();
    });
  });

  it('clears error when a file is selected', async () => {
    renderWithProviders(<TransformTips />);

    // Submit without file to trigger error
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Please select a file')).toBeInTheDocument();
    });

    // Select a file
    const fileInput = screen.getByLabelText(/select file/i);
    const testFile = new File(['test content'], 'test.csv', { type: 'text/csv' });

    fireEvent.change(fileInput, { target: { files: [testFile] } });

    await waitFor(() => {
      expect(screen.queryByText('Please select a file')).not.toBeInTheDocument();
    });
  });

  it('allows form submission when file is selected', async () => {
    renderWithProviders(<TransformTips />);

    // Select a file first
    const fileInput = screen.getByLabelText(/select file/i);
    const testFile = new File(['test content'], 'test.csv', { type: 'text/csv' });

    fireEvent.change(fileInput, { target: { files: [testFile] } });

    // Wait for state to update after file selection
    await waitFor(() => {
      expect(screen.queryByText('Please select a file')).not.toBeInTheDocument();
    });

    // Now submit form - should succeed without file validation error
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await userEvent.click(submitButton);

    // Should still not show file error after submission attempt
    expect(screen.queryByText('Please select a file')).not.toBeInTheDocument();
  });
});
