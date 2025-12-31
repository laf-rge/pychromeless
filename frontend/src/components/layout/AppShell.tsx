import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { TaskNotifications } from "../notifications/TaskNotifications";

interface AppShellProps {
  children: ReactNode;
  showSidebar?: boolean;
}

export function AppShell({ children, showSidebar = false }: AppShellProps) {
  return (
    <div className="flex flex-1">
      {showSidebar && <Sidebar />}
      <main className="flex-1">{children}</main>
      <TaskNotifications />
    </div>
  );
}
