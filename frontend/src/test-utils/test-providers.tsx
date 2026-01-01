import { ReactNode } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { render } from '@testing-library/react';
import { MsalProvider } from '@azure/msal-react';
import { createMockMsalInstance } from './test-helpers';

interface TestProvidersProps {
  children: ReactNode;
  msalInstance?: any;
  initialRoute?: string;
}

export function TestProviders({
  children,
  msalInstance = createMockMsalInstance(),
  initialRoute = '/',
}: TestProvidersProps) {
  // Set initial route if provided
  if (initialRoute !== '/') {
    window.history.pushState({}, '', initialRoute);
  }

  return (
    <MsalProvider instance={msalInstance}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </MsalProvider>
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
