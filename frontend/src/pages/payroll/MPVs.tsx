import { useMemo } from "react";
import { SubmitHandler } from "react-hook-form";
import { Feature } from "../../components/features/Feature";
import { useFormHandler } from "../../components/features/useFormHandler";
import { FormValues } from "../../components/features/types";
import { logger } from "../../utils/logger";
import { JosiahAlert } from "../../components/features/JosiahAlert";
import { DateAndPayPeriodControl } from "../../components/features/DateAndPayPeriodControl";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { useTaskStore } from "../../stores/taskStore";
import { OperationType } from "../../services/WebSocketService";
import { API_BASE_URL, API_ENDPOINTS } from "../../config/api";

export function MPVs() {
  // Access global task store to show operation-specific status
  const { activeTasks } = useTaskStore();

  // Get the latest MPVs task from global store
  const mpvsTask = useMemo(() => {
    const tasks = Array.from(activeTasks.values()).filter(
      (task) => task.operation === OperationType.GET_MPVS
    );
    // Return the most recent task
    return tasks.sort((a, b) => b.updated_at - a.updated_at)[0];
  }, [activeTasks]);
  const onSubmit: SubmitHandler<FormValues> = async (values) => {
    logger.debug(values);
  };

  const today = new Date();
  const currentMonth = {
    month: today.getMonth(),
    year: today.getFullYear(),
  };

  const {
    handleSubmit,
    register,
    errors,
    isSubmitting,
    isSubmitSuccessful,
    error,
    setValue,
    watch,
  } = useFormHandler(onSubmit, {
    baseURL: API_BASE_URL,
    endpoint: API_ENDPOINTS.GET_MPVS,
    formDataSubmission: true,
    defaultValues: {
      mp: currentMonth,
      pay_period: "0",
    },
  });

  const selectedMonth = watch("mp");

  const elevenMonthsAgo = new Date();
  elevenMonthsAgo.setMonth(today.getMonth() - 11);

  const isOlderThanElevenMonths = (selected: typeof currentMonth) => {
    const selectedDate = new Date(selected.year, selected.month);
    return selectedDate < elevenMonthsAgo;
  };

  const isFutureMonth = (selected: typeof currentMonth) => {
    const selectedDate = new Date(selected.year, selected.month);
    const firstOfCurrentMonth = new Date(today.getFullYear(), today.getMonth());
    return selectedDate > firstOfCurrentMonth;
  };

  return (
    <form onSubmit={handleSubmit}>
      <Feature
        title="Gusto MPVs"
        desc="Download the meal period violations for a valid pay period."
        isLoading={isSubmitting}
        type="submit"
      >
        <JosiahAlert
          error={error}
          isSuccess={isSubmitSuccessful}
          successMessage="Download is in progress. Check your downloads folder."
          taskStatus={mpvsTask}
        />
        <DateAndPayPeriodControl
          register={register}
          errors={errors}
          setValue={setValue}
          validate={{
            mp: {
              notFuture: (value) =>
                !isFutureMonth(value) || "Cannot select a future month",
            },
            pay_period: {
              required: (value: string) =>
                value ? true : "Please select a pay period",
              validate: (value) =>
                ["0", "1", "2"].includes(value) ||
                "Invalid pay period selected",
            },
          }}
        />
        {selectedMonth &&
          isOlderThanElevenMonths(selectedMonth) &&
          !errors.mp && (
            <Alert variant="warning" className="mt-2">
              <AlertDescription>
                Selected month is more than 11 months old. Please verify this is
                correct.
              </AlertDescription>
            </Alert>
          )}
      </Feature>
    </form>
  );
}
