import {
  InteractionRequiredAuthError,
  type IPublicClientApplication,
} from "@azure/msal-browser";
import { logger } from "../utils/logger";
import { OperationType } from "./WebSocketService";
import { API_BASE_URL } from "../config/api";

export interface TaskResult {
  success: boolean;
  message: string;
  failed_stores?: string[];
  successful_stores?: string[];
  [key: string]: unknown;
}

export interface TaskStatus {
  task_id: string;
  operation: OperationType;
  status: TaskStatusType;
  progress?: {
    current: number;
    total: number;
    message: string;
  };
  result?: TaskResult;
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
  private msalInstance: IPublicClientApplication;
  private readonly API_ENDPOINT = API_BASE_URL;

  private constructor(msalInstance: IPublicClientApplication) {
    this.msalInstance = msalInstance;
  }

  static getInstance(msalInstance: IPublicClientApplication): TaskStatusService {
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

  /**
   * Get recent tasks within the specified time window
   * @param hours Number of hours to look back (default: 24)
   * @param limit Maximum number of tasks to return (default: 50)
   * @returns Array of recent task statuses
   */
  async getRecentTasks(hours: number = 24, limit: number = 50): Promise<TaskStatus[]> {
    try {
      const response = await this.fetchWithAuth(
        `/task-status?recent=true&hours=${hours}&limit=${limit}`
      );
      return await response.json();
    } catch (error) {
      logger.error("Failed to fetch recent tasks:", error);
      throw error;
    }
  }
}

export default TaskStatusService;
