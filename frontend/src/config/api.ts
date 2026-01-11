/**
 * API Configuration
 * Centralized API endpoint configuration for the application
 */

/**
 * REST API Gateway base URL
 * Used for Lambda function invocations (operations like daily sales, invoice sync, etc.)
 */
export const API_BASE_URL = "https://uu7jn6wcdh.execute-api.us-east-2.amazonaws.com/production";

/**
 * WebSocket API Gateway URL
 * Used for real-time task status updates
 */
export const WS_BASE_URL = "wss://ozj082t179.execute-api.us-east-2.amazonaws.com/production";

/**
 * API Endpoints
 */
export const API_ENDPOINTS = {
  // Financial Operations
  DAILY_SALES: "",  // Root endpoint (no path)
  INVOICE_SYNC: "/invoice_sync",
  SPLIT_BILL: "/split_bill",
  FDMS_STATEMENT_IMPORT: "/fdms_statement_import",

  // Payroll Operations
  EMAIL_TIPS: "/email_tips",
  TRANSFORM_TIPS: "/transform_tips",
  GET_MPVS: "/get_mpvs",
  PAYROLL_ALLOCATION: "/payroll_allocation",
  GRUBHUB_CSV_IMPORT: "/grubhub_csv_import",

  // Utilities
  GET_FOOD_HANDLER_LINKS: "/get_food_handler_links",
  UPDATE_FOOD_HANDLER_PDFS: "/update_food_handler_pdfs",

  // Task Status
  TASK_STATUS: "/task-status",
} as const;
