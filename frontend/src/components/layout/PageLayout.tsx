import { ReactNode, useState } from "react";
import { useMsal } from "@azure/msal-react";
import { useLocation } from "react-router-dom";
import { NavBar } from "./NavBar";
import { Footer } from "./Footer";
import { Button } from "../ui/button";
import { IdTokenData } from "../DataDisplay";

interface PageLayoutProps {
  children: ReactNode;
}

const PUBLIC_ROUTES = ["/map", "/about", "/about-next", "/careers", "/locations"];

export function PageLayout({ children }: PageLayoutProps) {
  const { instance } = useMsal();
  const activeAccount = instance.getActiveAccount();
  const location = useLocation();
  const [showDebug, setShowDebug] = useState(false);

  const isPublicRoute = PUBLIC_ROUTES.includes(location.pathname);
  const isLightTheme = isPublicRoute || !activeAccount;

  return (
    <div className={`min-h-screen flex flex-col bg-background ${isLightTheme ? "theme-light" : "theme-dark"}`}>
      <NavBar />
      <div className="flex-1">{children}</div>
      <Footer />

      {/* Debug Panel - Only in Dev Mode */}
      {import.meta.env.DEV && activeAccount?.idTokenClaims && (
        <div className="fixed bottom-0 right-0 z-50 p-4">
          <div className="flex justify-end">
            <Button
              size="sm"
              variant={showDebug ? "default" : "outline"}
              onClick={() => setShowDebug(!showDebug)}
            >
              {showDebug ? "Hide" : "Show"} Debug Info
            </Button>
          </div>
          {showDebug && (
            <div className="mt-2 max-h-[400px] max-w-[90vw] overflow-auto rounded-md border border-border bg-card p-4 shadow-lg">
              <IdTokenData idTokenClaims={activeAccount.idTokenClaims} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
