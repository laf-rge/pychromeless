import {
  PublicClientApplication,
  EventType,
  EventMessage,
  AuthenticationResult,
  AccountInfo,
} from "@azure/msal-browser";
import { msalConfig } from "./authConfig";

export const msalInstance = new PublicClientApplication(msalConfig);

// Initialize MSAL
const initializeMsal = async () => {
  await msalInstance.initialize();

  // Set active account if exists
  const accounts = msalInstance.getAllAccounts();
  if (accounts.length > 0) {
    msalInstance.setActiveAccount(accounts[0]);
  }

  // Add event callback for authentication events
  msalInstance.addEventCallback((event: EventMessage) => {
    if (
      event.eventType === EventType.LOGIN_SUCCESS &&
      event.payload &&
      "account" in event.payload
    ) {
      const payload = event.payload as AuthenticationResult;
      const account: AccountInfo = payload.account;
      msalInstance.setActiveAccount(account);
      console.debug("Login successful, account set:", account.username);
    } else if (
      event.eventType === EventType.ACQUIRE_TOKEN_SUCCESS &&
      event.payload &&
      "account" in event.payload
    ) {
      const payload = event.payload as AuthenticationResult;
      console.debug("Token acquired successfully for:", payload.account?.username);
    } else if (event.eventType === EventType.ACQUIRE_TOKEN_FAILURE) {
      console.debug("Token acquisition failed:", event.error);
    } else if (event.eventType === EventType.SSO_SILENT_SUCCESS) {
      console.debug("Silent SSO successful");
    } else if (event.eventType === EventType.SSO_SILENT_FAILURE) {
      console.debug("Silent SSO failed:", event.error);
    }
  });
};

// Initialize immediately
initializeMsal().catch(console.error);

export { initializeMsal };
