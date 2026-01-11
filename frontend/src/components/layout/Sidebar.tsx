import { Link, useLocation } from "react-router-dom";
import { cn } from "../../utils/cn";

interface NavItem {
  name: string;
  href: string;
  icon?: React.ReactNode;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navigation: NavSection[] = [
  {
    title: "Main",
    items: [
      { name: "Dashboard", href: "/dashboard" },
    ],
  },
  {
    title: "Financial Operations",
    items: [
      { name: "Daily Sales", href: "/financial/daily-sales" },
      { name: "Invoice Sync", href: "/financial/invoice-sync" },
      { name: "Bill Split", href: "/financial/bill-split" },
      { name: "GrubHub Import", href: "/financial/grubhub-import" },
      { name: "FDMS Import", href: "/financial/fdms-import" },
    ],
  },
  {
    title: "Payroll & Tips",
    items: [
      { name: "Email Tips", href: "/payroll/email-tips" },
      { name: "Transform Tips", href: "/payroll/transform-tips" },
      { name: "Gusto MPVs", href: "/payroll/mpvs" },
      { name: "Payroll Allocation", href: "/payroll/allocation" },
    ],
  },
  {
    title: "Utilities",
    items: [
      { name: "Food Handler Links", href: "/utilities/food-handler-links" },
      ...(import.meta.env.DEV
        ? [{ name: "Error Tester", href: "/utilities/error-tester" }]
        : []),
    ],
  },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <div className="flex h-full w-64 flex-col border-r bg-card">
      <div className="flex h-16 items-center border-b px-6">
        <h1 className="text-xl font-semibold">WMC Admin</h1>
      </div>
      <nav className="flex-1 space-y-6 overflow-y-auto p-4">
        {navigation.map((section) => (
          <div key={section.title} className="space-y-2">
            <div className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground border-b border-border">
              {section.title}
            </div>
            <div className="space-y-1">
              {section.items.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className={cn(
                      "flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    {item.icon && <span className="mr-3">{item.icon}</span>}
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </div>
  );
}
