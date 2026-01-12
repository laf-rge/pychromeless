import { useMsal } from "@azure/msal-react";
import { Menu, Transition } from "@headlessui/react";
import axios from "axios";
import { Fragment, useEffect, useState } from "react";
import wmcLogo from "../../assets/WMC-logo.png";
import { graphConfig, loginRequest } from "../../authConfig";
import { Button } from "../ui/button";

const Links = [
  ["MyApps", "https://myapps.microsoft.com"],
  ["Behind the Counter", "https://franchisee.jerseymikes.com"],
  ["Flexepos", "https://fms.flexepos.com/FlexeposWeb/login.seam"],
  ["CrunchTime", "https://jerseymikes.net-chef.com/standalone/modern.ct#Login"],
];

export function NavBar() {
  const { instance, inProgress } = useMsal();
  const activeAccount = instance.getActiveAccount();
  const [imageUrl, setImageUrl] = useState<string>();

  useEffect(() => {
    // Wait for MSAL to finish any in-progress operations before fetching photo
    // This prevents race conditions where activeAccount is set but auth isn't complete
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

  return (
    <nav className="border-b bg-card">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <div className="flex items-center space-x-4">
          <a href="/" className="flex items-center">
            <img src={wmcLogo} alt="WMC logo" className="h-24 object-contain" />
          </a>
          {activeAccount && (
            <div className="flex space-x-2">
              {Links.map(([name, href], index) => (
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
          {!activeAccount ? (
            <Button variant="outline" onClick={handleLogin}>
              Sign In
            </Button>
          ) : (
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
                <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right rounded-md bg-popover shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
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
          )}
        </div>
      </div>
    </nav>
  );
}
