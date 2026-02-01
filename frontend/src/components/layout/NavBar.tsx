import { useMsal } from "@azure/msal-react";
import { Menu, Transition } from "@headlessui/react";
import axios from "axios";
import { Fragment, useCallback, useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu as MenuIcon, X } from "lucide-react";
import wmcLogo from "../../assets/WMC-logo.png";
import { graphConfig, loginRequest } from "../../authConfig";
import { Button } from "../ui/button";
import { useTaskStore } from "../../stores/taskStore";

const dashboardLinks = [
  ["MyApps", "https://myapps.microsoft.com"],
  ["Behind the Counter", "https://franchisee.jerseymikes.com"],
  ["Flexepos", "https://fms.flexepos.com/FlexeposWeb/login.seam"],
  ["CrunchTime", "https://jerseymikes.net-chef.com/standalone/modern.ct#Login"],
];

const publicNavLinks = [
  { label: "Locations", to: "/locations" },
  { label: "About", to: "/about" },
  { label: "Careers", to: "/careers" },
];

export function NavBar() {
  const { instance, inProgress } = useMsal();
  const activeAccount = instance.getActiveAccount();
  const location = useLocation();
  const [imageUrl, setImageUrl] = useState<string>();
  const isConnected = useTaskStore((state) => state.isConnected);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isPublicRoute = ["/", "/map", "/about", "/careers", "/locations"].includes(location.pathname);
  const isPublicView = !activeAccount || isPublicRoute;

  const closeMobileMenu = useCallback(() => setMobileMenuOpen(false), []);

  useEffect(() => {
    if (activeAccount && !imageUrl && inProgress === "none") {
      const accessTokenRequest = {
        scopes: ["user.read"],
        account: activeAccount,
      };

      instance
        .acquireTokenSilent(accessTokenRequest)
        .then((authenticationResult) => {
          const client = axios.create({
            baseURL: graphConfig.graphMeEndpoint,
          });
          return client.get("/photo/$value", {
            headers: {
              Authorization: "Bearer " + authenticationResult.accessToken,
            },
            responseType: "blob",
          });
        })
        .then((response) => {
          const url = window.URL || window.webkitURL;
          if (imageUrl) url.revokeObjectURL(imageUrl);
          const blobUrl = url.createObjectURL(response.data);
          setImageUrl(blobUrl);
        })
        .catch((error) => {
          console.error("Error fetching photo:", error);
        });
    }

    return () => {
      if (imageUrl) {
        const url = window.URL || window.webkitURL;
        url.revokeObjectURL(imageUrl);
      }
    };
  }, [activeAccount, instance, imageUrl, inProgress]);

  const handleLogin = async () => {
    try {
      if (instance.getActiveAccount() === null && inProgress === "none") {
        await instance.loginPopup(loginRequest);
      }
    } catch (error: unknown) {
      if (
        error &&
        typeof error === "object" &&
        ("errorCode" in error ||
          (error as { message?: string })?.message?.includes("popup") ||
          (error as { name?: string })?.name === "BrowserAuthError")
      ) {
        console.debug("Popup blocked, falling back to redirect");
        await instance.loginRedirect(loginRequest);
      } else {
        console.error("Login failed:", error);
      }
    }
  };

  const handleLogout = async () => {
    try {
      await instance.logoutPopup({
        postLogoutRedirectUri: window.location.origin,
      });
    } catch (error: unknown) {
      if (
        error &&
        typeof error === "object" &&
        ("errorCode" in error ||
          (error as { message?: string })?.message?.includes("popup") ||
          (error as { name?: string })?.name === "BrowserAuthError")
      ) {
        console.debug("Popup blocked, falling back to redirect");
        instance
          .logoutRedirect({
            onRedirectNavigate: () => false,
          })
          .catch((err: unknown) => console.error(err));
      } else {
        console.error("Logout failed:", error);
      }
    }
  };

  // Public navbar — light, warm, community-facing
  if (isPublicView && !activeAccount) {
    return (
      <>
        <nav className="border-b border-[#E8E2D6] bg-white">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center">
                <img
                  src={wmcLogo}
                  alt="WMC logo"
                  className="h-16 object-contain"
                  onError={(e) => { (e.target as HTMLImageElement).src = "/WMC-logo-only.png"; }}
                />
              </Link>
              {/* Desktop nav links */}
              <div className="hidden md:flex items-center gap-6">
                {publicNavLinks.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`font-heading text-sm font-medium transition-colors ${
                      location.pathname === link.to
                        ? "text-[#C8102E]"
                        : "text-[#2C2416] hover:text-[#C8102E]"
                    }`}
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                onClick={handleLogin}
                className="hidden md:inline-flex text-[#2C2416] hover:text-[#C8102E] hover:bg-[#F5F0E8]"
              >
                Sign In
              </Button>
              {/* Mobile hamburger */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 text-[#2C2416] hover:text-[#C8102E]"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? <X className="h-6 w-6" /> : <MenuIcon className="h-6 w-6" />}
              </button>
            </div>
          </div>

          {/* Mobile menu */}
          {mobileMenuOpen && (
            <div className="md:hidden border-t border-[#E8E2D6] bg-white px-4 py-4 space-y-1">
              {publicNavLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={closeMobileMenu}
                  className={`block font-heading rounded-md px-3 py-2.5 text-sm font-medium ${
                    location.pathname === link.to
                      ? "bg-[#F5F0E8] text-[#C8102E]"
                      : "text-[#2C2416] hover:bg-[#F5F0E8] hover:text-[#C8102E]"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
              <button
                onClick={() => { closeMobileMenu(); handleLogin(); }}
                className="block w-full text-left font-heading rounded-md px-3 py-2.5 text-sm font-medium text-[#2C2416] hover:bg-[#F5F0E8] hover:text-[#C8102E]"
              >
                Sign In
              </button>
            </div>
          )}
        </nav>
      </>
    );
  }

  // Authenticated navbar — dark dashboard variant
  return (
    <nav className="border-b bg-card">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <div className="flex items-center space-x-4">
          <a href="/" className="flex items-center">
            <img
              src={wmcLogo}
              alt="WMC logo"
              className="h-24 object-contain"
              onError={(e) => { (e.target as HTMLImageElement).src = "/WMC-logo-only.png"; }}
            />
          </a>
          {activeAccount && (
            <div className="hidden md:flex space-x-2">
              {dashboardLinks.map(([name, href], index) => (
                <a
                  key={index}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-foreground hover:text-primary"
                >
                  {name}
                </a>
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {/* Mobile hamburger for dashboard external links */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-foreground hover:text-primary"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <MenuIcon className="h-5 w-5" />}
          </button>

          {activeAccount && (
            <>
              {/* WebSocket connection status indicator */}
              <div
                className={`h-2 w-2 rounded-full ${isConnected ? "bg-success" : "bg-destructive"}`}
                title={isConnected ? "Real-time updates connected" : "Real-time updates disconnected"}
              />
              <Menu as="div" className="relative">
                <Menu.Button
                  as={Button}
                  variant="ghost"
                  className="flex items-center space-x-2"
                >
                  {imageUrl ? (
                    <img
                      src={imageUrl}
                      alt={activeAccount.name || "User"}
                      className="h-8 w-8 rounded-full"
                    />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-primary" />
                  )}
                </Menu.Button>
                <Transition
                  as={Fragment}
                  enter="transition ease-out duration-100"
                  enterFrom="transform opacity-0 scale-95"
                  enterTo="transform opacity-100 scale-100"
                  leave="transition ease-in duration-75"
                  leaveFrom="transform opacity-100 scale-100"
                  leaveTo="transform opacity-0 scale-95"
                >
                  <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right rounded-md bg-popover/95 shadow-lg ring-1 ring-black ring-opacity-5 backdrop-blur-sm focus:outline-none">
                    <div className="px-4 py-3">
                      <p className="text-sm font-medium">
                        {activeAccount.name || "Guest"}
                      </p>
                    </div>
                    <div className="border-t">
                      <Menu.Item>
                        {({ active }) => (
                          <a
                            href="https://myaccount.microsoft.com/?ref=MeControl"
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`block px-4 py-2 text-sm ${
                              active ? "bg-accent" : ""
                            }`}
                          >
                            Account Settings
                          </a>
                        )}
                      </Menu.Item>
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            onClick={handleLogout}
                            className={`block w-full px-4 py-2 text-left text-sm ${
                              active ? "bg-accent" : ""
                            }`}
                          >
                            Logout
                          </button>
                        )}
                      </Menu.Item>
                    </div>
                  </Menu.Items>
                </Transition>
              </Menu>
            </>
          )}
        </div>
      </div>

      {/* Mobile dashboard links */}
      {mobileMenuOpen && activeAccount && (
        <div className="md:hidden border-t border-border bg-card px-4 py-3 space-y-1">
          {dashboardLinks.map(([name, href], index) => (
            <a
              key={index}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-md px-3 py-2 text-sm text-foreground hover:bg-accent hover:text-accent-foreground"
            >
              {name}
            </a>
          ))}
        </div>
      )}
    </nav>
  );
}
