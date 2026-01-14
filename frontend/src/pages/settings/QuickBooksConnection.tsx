import { useState, useEffect, useCallback } from "react";
import { Feature } from "../../components/features/Feature";
import axios from "axios";
import { useMsal } from "@azure/msal-react";
import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { useToast } from "../../hooks/useToast";
import { Toast } from "../../components/ui/toast";
import { API_BASE_URL, API_ENDPOINTS } from "../../config/api";
import { Button } from "../../components/ui/button";
import { Spinner } from "../../components/ui/spinner";

// Only allow specific user to access this page
const ALLOWED_EMAIL = "william@wagonermanagement.com";

interface ConnectionStatus {
  connected: boolean;
  company_id?: string;
  message: string;
}

interface AuthUrlResponse {
  url: string;
  state: string;
}

export function QuickBooksConnection() {
  const [status, setStatus] = useState<ConnectionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const { instance } = useMsal();
  const { toast, toasts, removeToast } = useToast();

  const activeAccount = instance.getActiveAccount();
  const userEmail = activeAccount?.username?.toLowerCase() || "";
  const isAuthorized = userEmail === ALLOWED_EMAIL.toLowerCase();

  const getAuthToken = useCallback(async () => {
    const account = instance.getActiveAccount();
    if (!account) {
      throw new Error("No active account!");
    }

    try {
      const token = await instance.acquireTokenSilent({
        scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
        account,
      });
      return token.accessToken;
    } catch (error) {
      if (error instanceof InteractionRequiredAuthError) {
        const token = await instance.acquireTokenPopup({
          scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
          account,
        });
        return token.accessToken;
      }
      throw error;
    }
  }, [instance]);

  const fetchConnectionStatus = useCallback(async () => {
    if (!isAuthorized) return;

    setLoading(true);
    try {
      const token = await getAuthToken();
      const client = axios.create({ baseURL: API_BASE_URL });
      const response = await client.get<ConnectionStatus>(
        API_ENDPOINTS.QB_CONNECTION_STATUS,
        {
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setStatus(response.data);
    } catch (error) {
      console.error("Error fetching connection status:", error);
      toast({
        title: "Error",
        description: "Failed to fetch QuickBooks connection status",
        variant: "destructive",
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  }, [getAuthToken, isAuthorized, toast]);

  useEffect(() => {
    fetchConnectionStatus();
  }, [fetchConnectionStatus]);

  // Listen for messages from the OAuth popup
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Verify origin for security
      if (event.origin !== window.location.origin) return;

      if (event.data?.type === "QB_OAUTH_CALLBACK") {
        if (event.data.success) {
          toast({
            title: "Success",
            description: "QuickBooks connected successfully!",
            variant: "default",
            duration: 5000,
          });
          fetchConnectionStatus();
        } else {
          toast({
            title: "Error",
            description: event.data.error || "Failed to connect QuickBooks",
            variant: "destructive",
            duration: 5000,
          });
        }
        setConnecting(false);
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [fetchConnectionStatus, toast]);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const token = await getAuthToken();
      const client = axios.create({ baseURL: API_BASE_URL });
      const response = await client.get<AuthUrlResponse>(
        API_ENDPOINTS.QB_AUTH_URL,
        {
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );

      // Open popup centered on screen
      const width = 600;
      const height = 700;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;

      const popup = window.open(
        response.data.url,
        "QuickBooks OAuth",
        `width=${width},height=${height},left=${left},top=${top},scrollbars=yes`
      );

      if (!popup) {
        toast({
          title: "Error",
          description: "Popup blocked. Please allow popups for this site.",
          variant: "destructive",
          duration: 5000,
        });
        setConnecting(false);
      }
    } catch (error) {
      console.error("Error initiating OAuth:", error);
      toast({
        title: "Error",
        description: "Failed to initiate QuickBooks connection",
        variant: "destructive",
        duration: 5000,
      });
      setConnecting(false);
    }
  };

  if (!isAuthorized) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
          Access Denied
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          You do not have permission to access this page.
        </p>
      </div>
    );
  }

  return (
    <Feature
      title="QuickBooks Connection"
      desc="Manage your QuickBooks Online OAuth connection."
    >
      <div className="mt-6 space-y-6">
        {/* Connection Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Connection Status
          </h3>
          {loading ? (
            <div className="flex items-center gap-2">
              <Spinner size="sm" />
              <span className="text-gray-600 dark:text-gray-400">
                Checking connection...
              </span>
            </div>
          ) : status ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span
                  className={`inline-block w-3 h-3 rounded-full ${
                    status.connected ? "bg-green-500" : "bg-red-500"
                  }`}
                />
                <span className="text-gray-700 dark:text-gray-300">
                  {status.connected ? "Connected" : "Not Connected"}
                </span>
              </div>
              {status.company_id && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Company ID: {status.company_id}
                </p>
              )}
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {status.message}
              </p>
            </div>
          ) : (
            <p className="text-gray-600 dark:text-gray-400">
              Unable to check connection status
            </p>
          )}
        </div>

        {/* Connect Button */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            {status?.connected ? "Reconnect" : "Connect"} QuickBooks
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {status?.connected
              ? "Click to refresh your QuickBooks connection with new OAuth tokens."
              : "Click to connect your QuickBooks Online account using OAuth 2.0."}
          </p>
          <Button
            onClick={handleConnect}
            disabled={connecting}
            className="flex items-center gap-2"
          >
            {connecting ? (
              <>
                <Spinner size="sm" />
                Connecting...
              </>
            ) : (
              <>Connect to QuickBooks</>
            )}
          </Button>
        </div>

        {/* Important Notes */}
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
          <h4 className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-2">
            Important Notes
          </h4>
          <ul className="text-sm text-blue-700 dark:text-blue-300 list-disc list-inside space-y-1">
            <li>
              After connecting, the OAuth callback URL must be registered in
              your Intuit Developer App settings.
            </li>
            <li>
              QuickBooks tokens expire after 24 hours but are automatically
              refreshed during operations.
            </li>
            <li>
              If you see connection errors after connecting, check that the
              callback URL matches your API Gateway endpoint.
            </li>
          </ul>
        </div>
      </div>

      {/* Toast notifications */}
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onClose={() => removeToast(t.id)} />
      ))}
    </Feature>
  );
}
