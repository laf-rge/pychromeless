import { ReactNode, useState, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { PanelLeft, X } from "lucide-react";
import { Sidebar } from "./Sidebar";
import { TaskNotifications } from "../notifications/TaskNotifications";

interface AppShellProps {
  children: ReactNode;
  showSidebar?: boolean;
}

export function AppShell({ children, showSidebar = false }: AppShellProps) {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const location = useLocation();
  const closeSidebar = useCallback(() => setMobileSidebarOpen(false), []);

  // Close sidebar on route change
  const prevPath = location.pathname;
  if (mobileSidebarOpen && prevPath !== location.pathname) {
    setMobileSidebarOpen(false);
  }

  return (
    <div className="flex flex-1">
      {showSidebar && (
        <>
          {/* Desktop sidebar */}
          <div className="hidden lg:block">
            <Sidebar />
          </div>

          {/* Mobile sidebar toggle */}
          <button
            onClick={() => setMobileSidebarOpen(true)}
            className="lg:hidden fixed bottom-4 left-4 z-40 flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 active:scale-95"
            aria-label="Open sidebar"
          >
            <PanelLeft className="h-5 w-5" />
          </button>

          {/* Mobile sidebar overlay */}
          {mobileSidebarOpen && (
            <div className="lg:hidden fixed inset-0 z-50 flex">
              {/* Backdrop */}
              <div
                className="absolute inset-0 bg-black/50"
                onClick={closeSidebar}
              />
              {/* Sidebar panel */}
              <div className="relative z-10 flex">
                <Sidebar onNavigate={closeSidebar} />
                <button
                  onClick={closeSidebar}
                  className="ml-2 mt-3 flex h-8 w-8 items-center justify-center rounded-full bg-card text-foreground shadow-md"
                  aria-label="Close sidebar"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
      <main className="flex-1 min-w-0">{children}</main>
      <TaskNotifications />
    </div>
  );
}
