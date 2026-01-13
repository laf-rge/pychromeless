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
import { Alert, AlertDescription } from "../../components/ui/alert";
import { API_BASE_URL, API_ENDPOINTS } from "../../config/api";
import { useTaskStore } from "../../stores/taskStore";
import { OperationType } from "../../services/WebSocketService";

export function DailySales() {
  const createImmediateTask = useTaskStore((state) => state.createImmediateTask);

  const onSubmit: SubmitHandler<FormValues> = async (values) => {
    logger.debug(values);
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
    baseURL: API_BASE_URL,
    endpoint: API_ENDPOINTS.DAILY_SALES,
    formDataSubmission: false,
    defaultValues: {
      date: yesterday,
    },
    onSuccess: (data: { task_id?: string }) => {
      // Create immediate notification when API returns task_id
      if (data.task_id) {
        createImmediateTask(data.task_id, OperationType.DAILY_SALES);
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
