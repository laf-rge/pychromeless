import { useState } from "react";
import {
  FormControl,
  FormLabel,
  Input,
} from "../../components/ui";
import { Feature } from "../../components/features/Feature";
import axios from "axios";
import { useMsal } from "@azure/msal-react";
import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { Checkbox } from "../../components/ui/checkbox";
import { useToast } from "../../hooks/useToast";
import { Toast } from "../../components/ui/toast";

const AVAILABLE_LOCATIONS = [
  "20358",
  "20395",
  "20400",
  "20407",
  "WMC",
] as const;

export function BillSplit() {
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const { instance } = useMsal();
  const { toast, toasts, removeToast } = useToast();

  const handleSplitBill = async () => {
    if (!invoiceNumber.trim()) {
      toast({
        title: "Error",
        description: "Please enter an invoice number",
        variant: "destructive",
        duration: 3000,
      });
      return;
    }

    if (selectedLocations.length === 0) {
      toast({
        title: "Error",
        description: "Please select at least one location",
        variant: "destructive",
        duration: 3000,
      });
      return;
    }

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

      const response = await client.post(
        "test/split_bill",
        {
          doc_number: invoiceNumber,
          locations: selectedLocations,
        },
        config
      );

      toast({
        title: "Success",
        description:
          response.data.message ||
          "Bill split request has been submitted. Please allow a few minutes for the changes to appear in QuickBooks.",
        variant: "success",
        duration: 5000,
      });

      setInvoiceNumber("");
      setSelectedLocations([]);
    } catch (error) {
      const errorMessage = axios.isAxiosError(error)
        ? error.response?.data?.message || "Failed to submit bill split request"
        : "Failed to submit bill split request";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
        duration: 5000,
      });
      console.error("Error splitting bill:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLocationToggle = (location: string) => {
    setSelectedLocations((prev) =>
      prev.includes(location)
        ? prev.filter((l) => l !== location)
        : [...prev, location]
    );
  };

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
        title="Split Bill"
        desc="Enter an invoice number and select the locations to split the bill between. This will create separate bills in QuickBooks for each selected location."
        isLoading={loading}
        onClick={handleSplitBill}
        buttonText="Split Bill"
      >
        <div className="space-y-4">
          <FormControl>
            <FormLabel>Invoice Number</FormLabel>
            <Input
              value={invoiceNumber}
              onChange={(e) => setInvoiceNumber(e.target.value)}
              placeholder="Enter invoice number"
              disabled={loading}
            />
          </FormControl>

          <FormControl>
            <FormLabel>Select Locations</FormLabel>
            <div className="space-y-2">
              {AVAILABLE_LOCATIONS.map((location) => (
                <div key={location} className="flex items-center space-x-2">
                  <Checkbox
                    id={`location-${location}`}
                    checked={selectedLocations.includes(location)}
                    onChange={() => handleLocationToggle(location)}
                    disabled={loading}
                  />
                  <label
                    htmlFor={`location-${location}`}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    {location}
                  </label>
                </div>
              ))}
            </div>
          </FormControl>
        </div>
      </Feature>
    </>
  );
}
