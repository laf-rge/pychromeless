import { useState, useEffect } from "react";
import { Feature } from "../../components/features/Feature";
import axios from "axios";
import { useMsal } from "@azure/msal-react";
import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { useToast } from "../../hooks/useToast";
import { Toast } from "../../components/ui/toast";

interface FoodHandlerLinksResponse {
  [storeNumber: string]: string;
}

export function FoodHandlerLinks() {
  const [links, setLinks] = useState<FoodHandlerLinksResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const { instance } = useMsal();
  const { toast, toasts, removeToast } = useToast();

  const fetchLinks = async () => {
    setLoading(true);
    try {
      const account = instance.getActiveAccount();
      if (!account) {
        throw new Error("No active account!");
      }

      let token;
      try {
        token = await instance.acquireTokenSilent({
          scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
          account,
        });
      } catch (error) {
        if (error instanceof InteractionRequiredAuthError) {
          try {
            token = await instance.acquireTokenPopup({
              scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
              account,
            });
          } catch (popupError: unknown) {
            if (
              popupError &&
              typeof popupError === "object" &&
              ("errorCode" in popupError ||
                (popupError as { message?: string })?.message?.includes("popup") ||
                (popupError as { name?: string })?.name === "BrowserAuthError")
            ) {
              await instance.acquireTokenRedirect({
                scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
              });
              throw new Error("Authentication required. Please complete the redirect.");
            } else {
              throw popupError;
            }
          }
        } else {
          throw error;
        }
      }

      const client = axios.create({
        baseURL: "https://uu7jn6wcdh.execute-api.us-east-2.amazonaws.com/",
      });

      const config = {
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          Authorization: `Bearer ${token.accessToken}`,
        },
      };

      const response = await client.get<FoodHandlerLinksResponse>(
        "test/get_food_handler_links",
        config
      );

      setLinks(response.data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch food handler card links",
        variant: "destructive",
        duration: 5000,
      });
      console.error("Error fetching food handler links:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateLinks = async () => {
    setLoading(true);
    try {
      const account = instance.getActiveAccount();
      if (!account) {
        throw new Error("No active account!");
      }

      let token;
      try {
        token = await instance.acquireTokenSilent({
          scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
          account,
        });
      } catch (error) {
        if (error instanceof InteractionRequiredAuthError) {
          try {
            token = await instance.acquireTokenPopup({
              scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
              account,
            });
          } catch (popupError: unknown) {
            if (
              popupError &&
              typeof popupError === "object" &&
              ("errorCode" in popupError ||
                (popupError as { message?: string })?.message?.includes("popup") ||
                (popupError as { name?: string })?.name === "BrowserAuthError")
            ) {
              await instance.acquireTokenRedirect({
                scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
              });
              throw new Error("Authentication required. Please complete the redirect.");
            } else {
              throw popupError;
            }
          }
        } else {
          throw error;
        }
      }

      const client = axios.create({
        baseURL: "https://uu7jn6wcdh.execute-api.us-east-2.amazonaws.com/",
      });

      const config = {
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          Authorization: `Bearer ${token.accessToken}`,
        },
      };

      await client.post<FoodHandlerLinksResponse>(
        "test/update_food_handler_pdfs",
        {},
        config
      );

      toast({
        title: "Success",
        description: "Food handler PDFs will update in 2 minutes",
        variant: "success",
        duration: 5000,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send update request",
        variant: "destructive",
        duration: 5000,
      });
      console.error("Error updating food handler links:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLinks();
  }, []);

  return (
    <>
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map((toastItem) => (
          <Toast
            key={toastItem.id}
            {...toastItem}
            onClose={() => removeToast(toastItem.id)}
          />
        ))}
      </div>
      <Feature
        title="Food Handler Cards"
        desc="Update and view food handler card links for each store. The links will take you to the Google Drive PDF for each store's food handler cards."
        isLoading={loading}
        onClick={updateLinks}
        buttonText="Update"
      >
        {links && (
          <ul className="list-none space-y-2">
            {Object.entries(links).map(([storeNumber, link]) => (
              <li key={storeNumber}>
                <span>Store {storeNumber}: </span>
                <a
                  href={link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  View Food Handler Card
                </a>
              </li>
            ))}
          </ul>
        )}
      </Feature>
    </>
  );
}
