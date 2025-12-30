import { SubmitHandler } from "react-hook-form";
import {
  FormControl,
  FormLabel,
  FormMessage,
} from "../../components/ui";
import { Feature } from "../../components/features/Feature";
import { useFormHandler } from "../../components/features/useFormHandler";
import { FormValues } from "../../components/features/types";
import { logger } from "../../utils/logger";
import { JosiahAlert } from "../../components/features/JosiahAlert";
import { MonthPicker } from "../../components/ui/month-picker";
import { Alert, AlertDescription } from "../../components/ui/alert";

export function InvoiceSync() {
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
    errors,
    isSubmitting,
    isSubmitSuccessful,
    error,
    setValue,
    watch,
  } = useFormHandler(onSubmit, {
    baseURL: "https://uu7jn6wcdh.execute-api.us-east-2.amazonaws.com/",
    endpoint: "/test/invoice_sync",
    formDataSubmission: false,
    defaultValues: {
      mp: currentMonth,
    },
  });

  const selectedMonth = watch("mp");

  const isOlderThanOneMonth = (selected: typeof currentMonth) => {
    const selectedDate = new Date(selected.year, selected.month);
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);
    return selectedDate < oneMonthAgo;
  };

  return (
    <form onSubmit={handleSubmit}>
      <Feature
        title="Invoice Sync"
        desc="Sync the invoices from CrunchTime into Quickbooks."
        isLoading={isSubmitting}
        type="submit"
      >
        <JosiahAlert
          error={error}
          isSuccess={isSubmitSuccessful}
          successMessage="Invoice sync is in progress. Check Quickbooks in a few minutes."
        />
        <FormControl isInvalid={!!errors.mp}>
          <FormLabel htmlFor="date">Month</FormLabel>
          {selectedMonth && (
            <MonthPicker
              value={selectedMonth}
              onChange={(newValue) => setValue("mp", newValue)}
              lang="en-US"
            />
          )}
          <FormMessage>{errors.mp && errors.mp.message}</FormMessage>
        </FormControl>
        {selectedMonth && !errors.mp && (
          <>
            {isOlderThanOneMonth(selectedMonth) && (
              <Alert variant="warning" className="mt-2">
                <AlertDescription>
                  Selected month is more than 1 month old. Please verify this is
                  correct.
                </AlertDescription>
              </Alert>
            )}
          </>
        )}
      </Feature>
    </form>
  );
}
