import * as React from "react";
import { useState, useRef, useImperativeHandle, forwardRef } from "react";
import * as Popover from "@radix-ui/react-popover";
import { Button } from "./button";
import { MonthPickerValue } from "../features/types";
import { cn } from "../../utils/cn";

export interface MonthPickerProps {
  value: MonthPickerValue;
  onChange: (value: MonthPickerValue) => void;
  lang?: string;
}

export interface MonthPickerRef {
  focusButton: (index: number) => void;
}

const getMonthNames = ({
  locale = "en",
  format = "short",
}: {
  locale?: string;
  format?: "short" | "numeric" | "2-digit" | "long" | "narrow";
}) => {
  const currentYear = new Date().getFullYear();
  const formatter = new Intl.DateTimeFormat(locale, {
    month: format,
    timeZone: "UTC",
  });

  const months = [...Array(12).keys()].map(
    (monthIndex) => new Date(Date.UTC(currentYear, monthIndex, 1))
  );

  return months.map((date) => formatter.format(date));
};

export const MonthPicker = forwardRef<MonthPickerRef, MonthPickerProps>(
  ({ value, onChange, lang = "en-US" }, ref) => {
    const [isOpen, setIsOpen] = React.useState(false);
    const [month, setMonth] = useState<number>(
      value.month ?? new Date().getMonth()
    );
    const [year, setYear] = useState<number>(
      value.year ?? new Date().getFullYear()
    );
    const buttonRefs = useRef<Array<HTMLButtonElement | null>>([]);

    useImperativeHandle(ref, () => ({
      focusButton: (index: number) => {
        if (buttonRefs.current[index]) {
          buttonRefs.current[index]?.focus();
        }
      },
    }));

    const changeYear = (newYear: number) => {
      setYear(newYear);
    };

    const changeMonth = (newMonth: number) => {
      setMonth(newMonth);
      setIsOpen(false);
      onChange({
        month: newMonth,
        year: year,
      });
    };

    const monthNames = getMonthNames({ locale: lang, format: "short" });
    const displayValue = `${monthNames[value.month]} ${value.year}`;

    return (
      <Popover.Root open={isOpen} onOpenChange={setIsOpen}>
        <Popover.Trigger asChild>
          <Button
            variant="outline"
            className="w-full justify-start text-left font-normal"
          >
            {displayValue}
          </Button>
        </Popover.Trigger>
        <Popover.Portal>
          <Popover.Content
            className={cn(
              "z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none backdrop-blur-sm"
            )}
            align="start"
          >
            <div className="mb-4">
              <YearSelector year={year} onChange={changeYear} />
            </div>
            <div className="grid grid-cols-3 gap-2">
              {monthNames.map((monthName, index) => (
                <Button
                  key={index}
                  variant={index === month && value.year === year ? "default" : "ghost"}
                  size="sm"
                  onClick={() => changeMonth(index)}
                  ref={(el) => {
                    buttonRefs.current[index] = el;
                  }}
                >
                  {monthName}
                </Button>
              ))}
            </div>
            <Popover.Arrow className="fill-popover" />
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
    );
  }
);
MonthPicker.displayName = "MonthPicker";

function YearSelector({
  year,
  onChange,
}: {
  year: number;
  onChange: (year: number) => void;
}) {
  const currentYear = new Date().getFullYear();

  return (
    <div className="flex items-center justify-between">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onChange(year - 1)}
        disabled={year <= currentYear - 5}
      >
        ‹
      </Button>
      <span className="text-sm font-medium">{year}</span>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onChange(year + 1)}
        disabled={year >= currentYear + 5}
      >
        ›
      </Button>
    </div>
  );
}
