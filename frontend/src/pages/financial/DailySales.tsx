import React from "react";
import { SubmitHandler } from "react-hook-form";
import {
  FormControl,
  FormLabel,
  FormMessage,
  Input,
} from "../../components/ui";
import { Feature } from "../../components/features/Feature";
import { useFormHandler } from "../../components/features/useFormHandler";
import { FormValues } from "../../components/features/types";
import { logger } from "../../utils/logger";
import { JosiahAlert } from "../../components/features/JosiahAlert";
import { HARD_CUTOFF_DATE } from "../../components/features/constants";
import WebSocketService from "../../services/WebSocketService";
import { useMsal } from "@azure/msal-react";
import { Alert, AlertDescription } from "../../components/ui/alert";

type TaskStatus = {
  status?:
    | "started"
    | "processing"
    | "completed"
    | "completed_with_errors"
    | "failed";
  progress?: {
    current: number;
    total: number;
    message: string;
  };
  error?: string;
  result?: {
    success: boolean;
    message: string;
    failed_stores?: string[];
  };
};

export function DailySales() {
  const [taskStatus, setTaskStatus] = React.useState<TaskStatus>({});
  const { instance } = useMsal();

  const onSubmit: SubmitHandler<FormValues> = async (values) => {
    logger.debug(values);
    setTaskStatus({});
  };

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const yesterdayString = yesterday.toISOString().split("T")[0];

  const {
    handleSubmit,
    register,
    errors,
    isSubmitting,
    isSubmitSuccessful,
    error,
    watch,
  } = useFormHandler(onSubmit, {
    baseURL: "https://uu7jn6wcdh.execute-api.us-east-2.amazonaws.com/",
    endpoint: "/test",
    formDataSubmission: false,
    defaultValues: {
      date: yesterday,
    },
    onResponse: (response) => {
      console.log("Full API response:", response);
      const taskId = response.data.task_id;
      console.log("Received API response with task ID:", taskId);
      if (taskId) {
        const wsService = WebSocketService.getInstance(instance);
        console.log("Setting up WebSocket subscription for task:", taskId);
        wsService.subscribe(taskId, (payload) => {
          console.log("Received WebSocket update for task:", taskId, payload);
          setTaskStatus({
            status: payload.status === "error" ? "failed" : payload.status,
            progress: payload.progress,
            error: payload.error,
            result: payload.result,
          });
        });
      } else {
        console.warn("No task ID received in API response");
      }
    },
  });

  const selectedDate = watch("date");
  const twoMonthsAgo = new Date();
  twoMonthsAgo.setMonth(today.getMonth() - 2);
  const hardCutoffDate = HARD_CUTOFF_DATE;

  const dateToISOString = (date: Date | null | undefined): string => {
    if (!date) return yesterdayString;
    if (isNaN(date.getTime())) return yesterdayString;
    try {
      return date.toISOString().split("T")[0];
    } catch {
      return yesterdayString;
    }
  };

  const isValidDate = (date: Date | null | undefined): boolean => {
    if (!date) return false;
    return !isNaN(date.getTime());
  };

  return (
    <form onSubmit={handleSubmit}>
        <Feature
          title="Daily Sales"
          desc="Enter a valid date below and Josiah will update a days deposit and sales that you specify below. This is useful if you need to correct a deposit or payout/payin for a specific day in Quickbooks."
          isLoading={isSubmitting}
          type="submit"
        >
          <JosiahAlert
            error={error}
            isSuccess={isSubmitSuccessful}
            successMessage="Processing can take 2-5 minutes to appear in Quickbooks."
            taskStatus={taskStatus}
          />
          <FormControl isInvalid={!!errors.date}>
            <FormLabel htmlFor="date">Date</FormLabel>
            <Input
              id="date"
              type="date"
              max={yesterdayString}
              value={dateToISOString(selectedDate)}
              {...register("date", {
                required: "Please select a date",
                valueAsDate: true,
                validate: {
                  notToday: (value: Date | undefined) => {
                    if (!value) return "Please select a date";
                    const inputDate = new Date(value);
                    inputDate.setHours(0, 0, 0, 0);
                    return inputDate < today || "Cannot select today's date";
                  },
                  notBeforeCutoff: (value: Date | undefined) => {
                    if (!value) return "Please select a date";
                    return value >= hardCutoffDate ||
                      "Cannot select a date before January 1st, 2025";
                  },
                },
              })}
            />
            <FormMessage>{errors.date && errors.date.message}</FormMessage>
          </FormControl>
          {selectedDate &&
            isValidDate(selectedDate) &&
            selectedDate < twoMonthsAgo &&
            !errors.date && (
              <Alert variant="warning" className="mt-2">
                <AlertDescription>
                  Selected date is more than 2 months old. Please verify this is
                  correct.
                </AlertDescription>
              </Alert>
            )}
        </Feature>
      </form>
  );
}
