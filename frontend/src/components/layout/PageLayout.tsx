import { ReactNode, useState } from "react";
import { useMsal } from "@azure/msal-react";
import { NavBar } from "./NavBar";
import { Button } from "../ui/button";
import { IdTokenData } from "../DataDisplay";

interface PageLayoutProps {
  children: ReactNode;
}

export function PageLayout({ children }: PageLayoutProps) {
  const { instance } = useMsal();
  const activeAccount = instance.getActiveAccount();
  const [showDebug, setShowDebug] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <NavBar />
      {children}
      <footer className="border-t bg-card py-4 text-center text-sm text-muted-foreground">
        Copyright 2026, Wagoner Management Corp.
      </footer>

      {/* Debug Panel in Footer - Only in Dev Mode */}
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
