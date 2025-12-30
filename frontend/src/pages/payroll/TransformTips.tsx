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
import { DateAndPayPeriodControl } from "../../components/features/DateAndPayPeriodControl";
import { Alert, AlertDescription } from "../../components/ui/alert";

export function TransformTips() {
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
    endpoint: "/test/transform_tips",
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
        title="Gusto Tips Transform"
        desc="Upload a modified tips spreadsheet from above and this will return the CSV file you can use to upload."
        isLoading={isSubmitting}
        type="submit"
      >
        <JosiahAlert
          error={error}
          isSuccess={isSubmitSuccessful}
          successMessage="Download is in progress. Check your downloads folder."
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
              validOption: (value) =>
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
        <FormControl isInvalid={!!errors.file}>
          <FormLabel htmlFor="file">Select File:</FormLabel>
          <Input
            type="file"
            id="file"
            {...register("file", {
              required: "Please select a file",
              validate: {
                hasFile: (value: File | undefined) => {
                  if (!value) {
                    return "Please select a file";
                  }
                  return true;
                },
              },
              onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
                const file = e.target.files?.[0];
                if (file) {
                  setValue("file", file);
                }
              },
            })}
          />
          <FormMessage>{errors.file && errors.file.message}</FormMessage>
        </FormControl>
      </Feature>
    </form>
  );
}
