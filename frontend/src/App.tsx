import { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";
import { MsalProvider } from "@azure/msal-react";
import { msalInstance } from "./msal";
import { AppRoutes } from "./routes";
import { TestModeRoutes } from "./routes.test";
import WebSocketService from "./services/WebSocketService";
import { useTaskStore } from "./stores/taskStore";
import { logger } from "./utils/logger";
import { MockMsalProvider } from "./test-utils/MockMsalProvider";

// Check if we're in E2E test mode
const isE2ETestMode = import.meta.env.VITE_E2E_MODE === "true";

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
 */
function WebSocketInitializer() {
  const { setMsalInstance, handleTaskUpdate, setConnectionStatus } =
    useTaskStore();

  useEffect(() => {
    logger.debug("Initializing WebSocket global subscription");

    // Set MSAL instance in store for API calls
    setMsalInstance(msalInstance);

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
  }, [setMsalInstance, handleTaskUpdate, setConnectionStatus]);

  return null;
}

export default App;
