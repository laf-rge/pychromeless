import { useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { Spinner } from "../../components/ui/spinner";

/**
 * OAuth callback page for QuickBooks.
 * This page receives the redirect from the backend after OAuth token exchange.
 * It sends a postMessage to the opener window and closes itself.
 */
export function QBCallback() {
  const [searchParams] = useSearchParams();

  const success = searchParams.get("success") === "true";
  const error = searchParams.get("error");
  const isPopup = !!window.opener;

  // Compute message based on params - no need for state
  const message = useMemo(() => {
    if (isPopup) {
      return success
        ? "QuickBooks connected successfully! This window will close."
        : (error || "Connection failed. This window will close.");
    }
    return success
      ? "QuickBooks connected successfully! You can close this tab."
      : (error || "Connection failed. You can close this tab.");
  }, [success, error, isPopup]);

  useEffect(() => {
    // Send message to opener window
    if (window.opener) {
      window.opener.postMessage(
        {
          type: "QB_OAUTH_CALLBACK",
          success,
          error: error || undefined,
        },
        window.location.origin
      );

      // Close the popup after a short delay
      setTimeout(() => {
        window.close();
      }, 2000);
    }
  }, [success, error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 shadow-lg max-w-md text-center">
        {/* Status Icon */}
        <div className="mb-4">
          {success ? (
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900">
              <svg
                className="w-8 h-8 text-green-600 dark:text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          ) : (
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 dark:bg-red-900">
              <svg
                className="w-8 h-8 text-red-600 dark:text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
          )}
        </div>

        {/* Title */}
        <h1
          className={`text-xl font-semibold mb-2 ${
            success
              ? "text-green-700 dark:text-green-400"
              : "text-red-700 dark:text-red-400"
          }`}
        >
          {success ? "Connection Successful" : "Connection Failed"}
        </h1>

        {/* Message */}
        <p className="text-gray-600 dark:text-gray-400 mb-4">{message}</p>

        {/* Loading indicator */}
        {isPopup && (
          <div className="flex items-center justify-center gap-2 text-gray-500 dark:text-gray-400">
            <Spinner size="sm" />
            <span className="text-sm">Closing window...</span>
          </div>
        )}
      </div>
    </div>
  );
}
