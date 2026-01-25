import { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";
import { MsalProvider, useMsal } from "@azure/msal-react";
import { msalInstance } from "./msal";
import { AppRoutes } from "./routes";
import { TestModeRoutes } from "./routes.e2e";
import WebSocketService from "./services/WebSocketService";
import { useTaskStore } from "./stores/taskStore";
import { logger } from "./utils/logger";
import { MockMsalProvider } from "./test-utils/MockMsalProvider";

// Check if we're in E2E test mode
const isE2ETestMode = import.meta.env.BUN_E2E_MODE === "true";

function App() {
  if (isE2ETestMode) {
    return (
      <MockMsalProvider>
        <BrowserRouter>
          <TestModeRoutes />
        </BrowserRouter>
      </MockMsalProvider>
    );
  }

  return (
    <MsalProvider instance={msalInstance}>
      <BrowserRouter>
        <WebSocketInitializer />
        <AppRoutes />
      </BrowserRouter>
    </MsalProvider>
  );
}

/**
 * Component to initialize WebSocket global subscription
 * Separated to ensure it runs within MsalProvider context
 * Only initializes WebSocket when user is authenticated
 */
function WebSocketInitializer() {
  const { instance, accounts } = useMsal();
  const isAuthenticated = accounts.length > 0;
  const { setMsalInstance, handleTaskUpdate, setConnectionStatus } =
    useTaskStore();

  useEffect(() => {
    // Set MSAL instance in store for API calls (always needed)
    setMsalInstance(msalInstance);

    // Don't initialize WebSocket until user is authenticated
    if (!isAuthenticated) {
      logger.debug("Skipping WebSocket initialization - user not authenticated");
      return;
    }

    // Ensure active account is set (needed for token acquisition)
    if (!instance.getActiveAccount() && accounts[0]) {
      instance.setActiveAccount(accounts[0]);
    }

    logger.debug("Initializing WebSocket global subscription");

    // Initialize WebSocket service
    const wsService = WebSocketService.getInstance(msalInstance);

    // Subscribe to connection status changes
    const unsubscribeConnection = wsService.onConnectionChange((connected) => {
      logger.debug(`WebSocket connection status: ${connected}`);
      setConnectionStatus(connected);
    });

    // Subscribe to all task updates globally
    const unsubscribeGlobal = wsService.subscribeGlobal((payload) => {
      logger.debug("Global task update received", payload);
      handleTaskUpdate(payload);
    });

    // Task history is loaded by Dashboard when user navigates to it

    // Cleanup on unmount
    return () => {
      logger.debug("Cleaning up WebSocket subscriptions");
      unsubscribeConnection();
      unsubscribeGlobal();
    };
  }, [isAuthenticated, instance, accounts, setMsalInstance, handleTaskUpdate, setConnectionStatus]);

  return null;
}

export default App;
