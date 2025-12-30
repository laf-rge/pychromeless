import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useMsal } from "@azure/msal-react";
import { Spinner } from "../ui/spinner";

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { instance, inProgress } = useMsal();
  const activeAccount = instance.getActiveAccount();

  if (inProgress !== "none" && inProgress !== "startup") {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!activeAccount) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
