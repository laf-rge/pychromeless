import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  DollarSign,
  RefreshCw,
  Scissors,
  Upload,
  FileUp,
  Mail,
  ArrowRightLeft,
  Users,
  PieChart,
  ClipboardCheck,
  AlertTriangle,
  Settings,
} from "lucide-react";
import { cn } from "../../utils/cn";

interface NavItem {
  name: string;
  href: string;
  icon: React.ReactNode;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navigation: NavSection[] = [
  {
    title: "Main",
    items: [
      { name: "Dashboard", href: "/dashboard", icon: <LayoutDashboard className="h-4 w-4" /> },
    ],
  },
  {
    title: "Financial Operations",
    items: [
      { name: "Daily Sales", href: "/financial/daily-sales", icon: <DollarSign className="h-4 w-4" /> },
      { name: "Invoice Sync", href: "/financial/invoice-sync", icon: <RefreshCw className="h-4 w-4" /> },
      { name: "Bill Split", href: "/financial/bill-split", icon: <Scissors className="h-4 w-4" /> },
      { name: "GrubHub Import", href: "/financial/grubhub-import", icon: <Upload className="h-4 w-4" /> },
      { name: "FDMS Import", href: "/financial/fdms-import", icon: <FileUp className="h-4 w-4" /> },
    ],
  },
  {
    title: "Payroll & Tips",
    items: [
      { name: "Email Tips", href: "/payroll/email-tips", icon: <Mail className="h-4 w-4" /> },
      { name: "Transform Tips", href: "/payroll/transform-tips", icon: <ArrowRightLeft className="h-4 w-4" /> },
      { name: "Gusto MPVs", href: "/payroll/mpvs", icon: <Users className="h-4 w-4" /> },
      { name: "Payroll Allocation", href: "/payroll/allocation", icon: <PieChart className="h-4 w-4" /> },
    ],
  },
  {
    title: "Utilities",
    items: [
      { name: "Food Handler Links", href: "/utilities/food-handler-links", icon: <ClipboardCheck className="h-4 w-4" /> },
      ...(import.meta.env.DEV
        ? [{ name: "Error Tester", href: "/utilities/error-tester", icon: <AlertTriangle className="h-4 w-4" /> }]
        : []),
    ],
  },
  {
    title: "Settings",
    items: [
      { name: "QuickBooks", href: "/settings/quickbooks", icon: <Settings className="h-4 w-4" /> },
    ],
  },
];

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const location = useLocation();

  return (
    <div className="flex h-full w-64 flex-col border-r bg-card">
      <div className="flex h-14 items-center border-b px-6">
        <h1 className="text-lg font-semibold">WMC Admin</h1>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto p-4">
        {navigation.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground border-b border-border">
              {section.title}
            </div>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={onNavigate}
                    className={cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    <span className={cn(
                      "flex-shrink-0",
                      isActive ? "text-primary-foreground" : "text-muted-foreground"
                    )}>
                      {item.icon}
                    </span>
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
