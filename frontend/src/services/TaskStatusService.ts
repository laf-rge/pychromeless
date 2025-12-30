import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { logger } from "../utils/logger";
import { OperationType } from "./WebSocketService";

export interface TaskStatus {
  task_id: string;
  operation: OperationType;
  status: TaskStatusType;
  progress?: {
    current: number;
    total: number;
    message: string;
  };
  result?: any;
  error?: string;
  created_at: number;
  updated_at: number;
}

export type TaskStatusType =
  | "started"
  | "processing"
  | "error"
  | "completed"
  | "completed_with_errors"
  | "failed";

class TaskStatusService {
  private static instance: TaskStatusService;
  private msalInstance: any;
  private readonly API_ENDPOINT =
    "https://ozj082t179.execute-api.us-east-2.amazonaws.com/production";

  private constructor(msalInstance: any) {
    this.msalInstance = msalInstance;
  }

  static getInstance(msalInstance: any): TaskStatusService {
    if (!TaskStatusService.instance) {
      TaskStatusService.instance = new TaskStatusService(msalInstance);
    }
    return TaskStatusService.instance;
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

  private async fetchWithAuth(endpoint: string): Promise<Response> {
    const accessToken = await this.getAccessToken();
    const response = await fetch(`${this.API_ENDPOINT}${endpoint}`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      logger.error(`API request failed: ${error}`);
      throw new Error(`API request failed: ${error}`);
    }

    return response;
  }

  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    try {
      const response = await this.fetchWithAuth(`/task-status/${taskId}`);
      return await response.json();
    } catch (error) {
      logger.error(`Failed to fetch task status for ${taskId}:`, error);
      throw error;
    }
  }

  async getTasksByOperation(operation: OperationType): Promise<TaskStatus[]> {
    try {
      const response = await this.fetchWithAuth(
        `/task-status?operation=${operation}`
      );
      return await response.json();
    } catch (error) {
      logger.error(`Failed to fetch tasks for operation ${operation}:`, error);
      throw error;
    }
  }

  async getAllTasks(): Promise<TaskStatus[]> {
    try {
      const response = await this.fetchWithAuth("/task-status");
      return await response.json();
    } catch (error) {
      logger.error("Failed to fetch all tasks:", error);
      throw error;
    }
  }
}

export default TaskStatusService;
