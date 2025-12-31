import { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";
import { MsalProvider } from "@azure/msal-react";
import { msalInstance } from "./msal";
import { AppRoutes } from "./routes";
import WebSocketService from "./services/WebSocketService";
import { useTaskStore } from "./stores/taskStore";
import { logger } from "./utils/logger";

function App() {
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
  const { setMsalInstance, handleTaskUpdate, setConnectionStatus, loadTaskHistory } =
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

    // Load task history from backend on mount
    loadTaskHistory();

    // Cleanup on unmount
    return () => {
      logger.debug("Cleaning up WebSocket subscriptions");
      unsubscribeConnection();
      unsubscribeGlobal();
    };
  }, [setMsalInstance, handleTaskUpdate, setConnectionStatus, loadTaskHistory]);

  return null;
}

export default App;
