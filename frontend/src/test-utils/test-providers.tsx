/* eslint-disable react-refresh/only-export-components */
import { ReactNode } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { render } from '@testing-library/react';
import { MockMsalProvider } from './MockMsalProvider';

interface TestProvidersProps {
  children: ReactNode;
  initialRoute?: string;
}

export function TestProviders({
  children,
  initialRoute = '/',
}: TestProvidersProps) {
  // Set initial route if provided
  if (initialRoute !== '/') {
    window.history.pushState({}, '', initialRoute);
  }

  return (
    <MockMsalProvider>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </MockMsalProvider>
  );
}

// Custom render with providers
export function renderWithProviders(
  ui: ReactNode,
  options: Omit<TestProvidersProps, 'children'> = {}
) {
  return render(ui, {
    wrapper: ({ children }) => (
      <TestProviders {...options}>{children}</TestProviders>
    ),
  });
}
