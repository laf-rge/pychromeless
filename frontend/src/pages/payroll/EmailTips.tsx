import { SubmitHandler } from "react-hook-form";
import { Feature } from "../../components/features/Feature";
import { useFormHandler } from "../../components/features/useFormHandler";
import { FormValues } from "../../components/features/types";
import { logger } from "../../utils/logger";
import { JosiahAlert } from "../../components/features/JosiahAlert";
import { DateAndPayPeriodControl } from "../../components/features/DateAndPayPeriodControl";
import { Alert, AlertDescription } from "../../components/ui/alert";

export function EmailTips() {
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
    baseURL: "https://uu7jn6wcdh.execute-api.us-east-2.amazonaws.com/",
    endpoint: "/test/email_tips",
    formDataSubmission: false,
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
        title="Email Tips"
        desc="Get the tips for a valid pay period via email."
        isLoading={isSubmitting}
        type="submit"
      >
        <JosiahAlert
          error={error}
          isSuccess={isSubmitSuccessful}
          successMessage="Processing can take 2-5 minutes to appear in your email."
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
              validOption: (value: string) =>
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
