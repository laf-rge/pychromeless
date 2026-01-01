/* eslint-disable react-refresh/only-export-components */
import { ReactNode, createContext, useContext } from "react";
import type { AccountInfo, IPublicClientApplication } from "@azure/msal-browser";

// Mock account for testing
export const mockAccount: AccountInfo = {
  homeAccountId: "test-home-id",
  environment: "login.windows.net",
  tenantId: "test-tenant-id",
  username: "test@example.com",
  localAccountId: "test-local-id",
  name: "Test User",
  idTokenClaims: {
    oid: "test-oid",
    sub: "test-sub",
    name: "Test User",
    preferred_username: "test@example.com",
  },
};

// Mock MSAL instance
export const mockMsalInstance: Partial<IPublicClientApplication> = {
  getActiveAccount: () => mockAccount,
  getAllAccounts: () => [mockAccount],
  setActiveAccount: () => {},
  acquireTokenSilent: async () => ({
    accessToken: "mock-access-token",
    account: mockAccount,
    authority: "https://login.microsoftonline.com/test-tenant-id",
    uniqueId: "test-unique-id",
    tenantId: "test-tenant-id",
    scopes: ["api://test-scope"],
    idToken: "mock-id-token",
    idTokenClaims: mockAccount.idTokenClaims!,
    fromCache: true,
    expiresOn: new Date(Date.now() + 3600000),
    extExpiresOn: new Date(Date.now() + 7200000),
    tokenType: "Bearer",
    correlationId: "test-correlation-id",
  }),
  loginPopup: async () => ({
    accessToken: "mock-access-token",
    account: mockAccount,
    authority: "https://login.microsoftonline.com/test-tenant-id",
    uniqueId: "test-unique-id",
    tenantId: "test-tenant-id",
    scopes: ["api://test-scope"],
    idToken: "mock-id-token",
    idTokenClaims: mockAccount.idTokenClaims!,
    fromCache: false,
    expiresOn: new Date(Date.now() + 3600000),
    extExpiresOn: new Date(Date.now() + 7200000),
    tokenType: "Bearer",
    correlationId: "test-correlation-id",
  }),
  loginRedirect: async () => {},
  logout: async () => {},
  logoutPopup: async () => {},
  logoutRedirect: async () => {},
};

// Context for mock MSAL
interface MockMsalContextValue {
  instance: Partial<IPublicClientApplication>;
  accounts: AccountInfo[];
  inProgress: string;
}

const MockMsalContext = createContext<MockMsalContextValue>({
  instance: mockMsalInstance,
  accounts: [mockAccount],
  inProgress: "none",
});

// Mock useMsal hook
export function useMockMsal() {
  return useContext(MockMsalContext);
}

// Mock MsalProvider for tests
interface MockMsalProviderProps {
  children: ReactNode;
}

export function MockMsalProvider({ children }: MockMsalProviderProps) {
  return (
    <MockMsalContext.Provider
      value={{
        instance: mockMsalInstance,
        accounts: [mockAccount],
        inProgress: "none",
      }}
    >
      {children}
    </MockMsalContext.Provider>
  );
}

// Mock AuthenticatedTemplate - always renders children in test mode
export function MockAuthenticatedTemplate({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

// Mock UnauthenticatedTemplate - never renders in test mode
export function MockUnauthenticatedTemplate(_props: { children: ReactNode }) {
  return null;
}
