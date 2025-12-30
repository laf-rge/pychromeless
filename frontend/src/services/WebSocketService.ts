import { logger } from "../utils/logger";
import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { TaskStatus } from "./TaskStatusService";

export enum OperationType {
  DAILY_SALES = "daily_sales",
  INVOICE_SYNC = "invoice_sync",
  EMAIL_TIPS = "email_tips",
  UPDATE_FOOD_HANDLER_PDFS = "update_food_handler_pdfs",
  TRANSFORM_TIPS = "transform_tips",
  GET_MPVS = "get_mpvs",
  GET_FOOD_HANDLER_LINKS = "get_food_handler_links",
}

export const OperationDisplayNames: Record<OperationType, string> = {
  [OperationType.DAILY_SALES]: "Daily Sales Processing",
  [OperationType.INVOICE_SYNC]: "Invoice Synchronization",
  [OperationType.EMAIL_TIPS]: "Tips Email Generation",
  [OperationType.UPDATE_FOOD_HANDLER_PDFS]: "Food Handler PDF Update",
  [OperationType.TRANSFORM_TIPS]: "Tips Transformation",
  [OperationType.GET_MPVS]: "Meal Period Violations",
  [OperationType.GET_FOOD_HANDLER_LINKS]: "Food Handler PDF Links",
};

interface EnrichedTaskStatus extends TaskStatus {
  operationDisplayName: string;
}

type MessageHandler = (message: EnrichedTaskStatus) => void;
interface WebSocketMessage {
  type: "task_status";
  payload: TaskStatus;
}

class WebSocketService {
  private static instance: WebSocketService;
  private ws: WebSocket | null = null;
  private subscribers: Map<string, Set<MessageHandler>> = new Map();
  private messageQueue: Map<string, any[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout = 1000;
  private msalInstance: any;
  private isConnected = false;
  private isReconnecting = false;
  private reconnectTimer: number | null = null;
  private connectionListeners: Set<(connected: boolean) => void> = new Set();

  private constructor(msalInstance: any) {
    this.msalInstance = msalInstance;
    this.connect();
  }

  static getInstance(msalInstance: any): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService(msalInstance);
    }
    return WebSocketService.instance;
  }

  private async getAccessToken(): Promise<string> {
    if (!this.msalInstance) {
      throw new Error("MSAL instance not found");
    }

    const activeAccount = this.msalInstance.getActiveAccount();
    if (!activeAccount) {
      throw new Error("No active account found");
    }

    const accessTokenRequest = {
      scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
      account: activeAccount,
    };

    try {
      const response = await this.msalInstance.acquireTokenSilent(
        accessTokenRequest
      );
      return response.accessToken;
    } catch (error) {
      if (error instanceof InteractionRequiredAuthError) {
        try {
          await this.msalInstance.acquireTokenPopup({
            scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
            account: activeAccount,
          });
          const response = await this.msalInstance.acquireTokenSilent(
            accessTokenRequest
          );
          return response.accessToken;
        } catch (popupError: unknown) {
          if (
            popupError &&
            typeof popupError === "object" &&
            ("errorCode" in popupError ||
              (popupError as { message?: string })?.message?.includes("popup") ||
              (popupError as { name?: string })?.name === "BrowserAuthError")
          ) {
            logger.debug("Popup blocked, falling back to redirect");
            await this.msalInstance.acquireTokenRedirect({
              scopes: ["api://32483067-a12e-43ba-a194-a4a6e0a579b2/WMCWeb.Josiah"],
            });
          }
          throw popupError;
        }
      }
      throw error;
    }
  }

  isWebSocketConnected(): boolean {
    return this.isConnected;
  }

  onConnectionChange(listener: (connected: boolean) => void): () => void {
    this.connectionListeners.add(listener);
    listener(this.isConnected);
    return () => this.connectionListeners.delete(listener);
  }

  async reconnect(): Promise<void> {
    if (this.isReconnecting) {
      console.log("Already attempting to reconnect");
      return;
    }

    console.log("Manual reconnection requested");
    this.isReconnecting = true;
    this.reconnectAttempts = 0;
    this.isConnected = false;
    this.notifyConnectionChange(false);

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    try {
      await this.connect();
    } catch (error) {
      console.error("Manual reconnection failed:", error);
      this.handleReconnect();
    }
  }

  private notifyConnectionChange(connected: boolean) {
    this.isConnected = connected;
    this.connectionListeners.forEach((listener) => listener(connected));
  }

  private async connect() {
    console.log("Connecting to WebSocket...");
    try {
      const accessToken = await this.getAccessToken();
      const WS_ENDPOINT =
        "wss://ozj082t179.execute-api.us-east-2.amazonaws.com/production";
      const wsUrl = `${WS_ENDPOINT}?Authorization=${encodeURIComponent(
        `Bearer ${accessToken}`
      )}`;
      console.log("Connecting to WebSocket with URL:", wsUrl);
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("WebSocket connected successfully");
        logger.debug("WebSocket connected");
        this.reconnectAttempts = 0;
        this.isReconnecting = false;
        this.notifyConnectionChange(true);
        this.processQueuedMessages();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log("Received WebSocket message:", message);
          if (message.type === "task_status") {
            const taskId = message.payload.task_id;
            const operation = message.payload.operation;
            console.log(
              `Processing message for task ${taskId} (${OperationDisplayNames[operation]})`
            );

            const subscribers = this.subscribers.get(taskId);
            if (subscribers) {
              console.log(
                `Found ${subscribers.size} subscribers for task ${taskId}`
              );
              const enrichedPayload: EnrichedTaskStatus = {
                ...message.payload,
                operationDisplayName: OperationDisplayNames[operation],
              };
              subscribers.forEach((handler) => handler(enrichedPayload));
            } else {
              console.log(
                `No subscribers found for task ${taskId}, queueing message`
              );
              if (!this.messageQueue.has(taskId)) {
                this.messageQueue.set(taskId, []);
              }
              this.messageQueue.get(taskId)!.push(message.payload);
            }
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
          logger.error("Error parsing WebSocket message:", error);
        }
      };

      this.ws.onclose = (event) => {
        console.log("WebSocket disconnected", {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
        });
        logger.debug("WebSocket disconnected", {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
        });
        this.notifyConnectionChange(false);
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        logger.error("WebSocket error:", error);
        this.notifyConnectionChange(false);
      };
    } catch (error) {
      console.error("Error in WebSocket connect:", error);
      logger.error("Error in WebSocket connect:", error);
      this.notifyConnectionChange(false);
      throw error;
    }
  }

  private processQueuedMessages() {
    console.log("Processing queued messages...");
    for (const [taskId, messages] of this.messageQueue.entries()) {
      const subscribers = this.subscribers.get(taskId);
      if (subscribers) {
        console.log(
          `Processing ${messages.length} queued messages for task ${taskId}`
        );
        messages.forEach((message) => {
          subscribers.forEach((handler) => handler(message));
        });
        this.messageQueue.delete(taskId);
      }
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      this.notifyConnectionChange(false);
      this.reconnectAttempts = 0;
      this.reconnectTimer = setTimeout(() => this.connect(), 30000);
      return;
    }

    this.reconnectAttempts++;
    const delay =
      this.reconnectTimeout * Math.pow(2, this.reconnectAttempts - 1);
    console.log(
      `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms...`
    );

    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  subscribe(taskId: string, handler: MessageHandler): () => void {
    console.log(`Subscribing to task: ${taskId}`);
    if (!this.subscribers.has(taskId)) {
      this.subscribers.set(taskId, new Set());
      console.log(`Created new subscription set for task ${taskId}`);
    }
    this.subscribers.get(taskId)!.add(handler);
    console.log(
      `Current subscribers for task ${taskId}: ${
        this.subscribers.get(taskId)!.size
      }`
    );

    if (this.isConnected && this.messageQueue.has(taskId)) {
      const messages = this.messageQueue.get(taskId)!;
      console.log(
        `Processing ${messages.length} queued messages for task ${taskId}`
      );
      messages.forEach((message) => {
        handler(message);
      });
      this.messageQueue.delete(taskId);
    }

    return () => {
      console.log(`Unsubscribing from task: ${taskId}`);
      const subscribers = this.subscribers.get(taskId);
      if (subscribers) {
        subscribers.delete(handler);
        if (subscribers.size === 0) {
          this.subscribers.delete(taskId);
          console.log(`Removed empty subscription set for task ${taskId}`);
        }
      }
    };
  }
}

export default WebSocketService;
