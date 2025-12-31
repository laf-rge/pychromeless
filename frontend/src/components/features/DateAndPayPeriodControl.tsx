import React, { useState, useCallback, useEffect } from "react";
import {
  FormControl,
  FormLabel,
  FormMessage,
} from "../ui/form";
import { MonthPicker } from "../ui/month-picker";
import { DateAndPayPeriodProps, MonthPickerValue } from "./types";

export const DateAndPayPeriodControl: React.FC<DateAndPayPeriodProps> = ({
  register,
  setValue,
  errors,
  validate,
}) => {
  const [selectedMonthData, setSelectedMonthData] = useState<MonthPickerValue>({
    month: new Date().getUTCMonth(),
    year: new Date().getUTCFullYear(),
  });

  useEffect(() => {
    setValue("mp", selectedMonthData);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setValue]);

  const handleChange = useCallback(
    (newValue: MonthPickerValue) => {
      setSelectedMonthData(newValue);
      setValue("mp", newValue);
    },
    [setValue]
  );

  return (
    <>
      <FormControl isInvalid={!!errors.mp}>
        <FormLabel htmlFor="date">Month</FormLabel>
        <MonthPicker
          value={selectedMonthData}
          onChange={handleChange}
          lang="en-US"
        />
        <FormMessage>{errors.mp && errors.mp.message}</FormMessage>
      </FormControl>
      <FormControl isInvalid={!!errors.pay_period}>
        <FormLabel>Pay Period</FormLabel>
        <div className="flex space-x-4">
          <div className="flex items-center space-x-2">
            <input
              type="radio"
              id="pay_period_0"
              value="0"
              {...register("pay_period", validate?.pay_period)}
              className="h-4 w-4"
            />
            <label htmlFor="pay_period_0" className="text-sm">
              Entire Month
            </label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="radio"
              id="pay_period_1"
              value="1"
              {...register("pay_period", validate?.pay_period)}
              className="h-4 w-4"
            />
            <label htmlFor="pay_period_1" className="text-sm">
              1st
            </label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="radio"
              id="pay_period_2"
              value="2"
              {...register("pay_period", validate?.pay_period)}
              className="h-4 w-4"
            />
            <label htmlFor="pay_period_2" className="text-sm">
              2nd
            </label>
          </div>
        </div>
        <FormMessage>
          {errors.pay_period && errors.pay_period.message}
        </FormMessage>
      </FormControl>
    </>
  );
};

export default DateAndPayPeriodControl;
