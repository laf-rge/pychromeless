import React, { useState } from "react";
import { SubmitHandler } from "react-hook-form";
import {
  FormControl,
  FormLabel,
  FormMessage,
  FileInput,
} from "../../components/ui";
import { Feature } from "../../components/features/Feature";
import { useFormHandler } from "../../components/features/useFormHandler";
import { FormValues } from "../../components/features/types";
import { logger } from "../../utils/logger";
import { JosiahAlert } from "../../components/features/JosiahAlert";
import { MonthPicker } from "../../components/features/MonthPicker";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { API_BASE_URL, API_ENDPOINTS } from "../../config/api";

interface PayrollAllocationResult {
  success: boolean;
  journal_entry_url?: string;
  doc_number?: string;
  summary?: {
    stores_processed: string[];
    total_gross_earnings: string;
    total_employer_taxes: string;
  };
  warnings?: Array<{
    type: string;
    message: string;
    amount: string;
  }>;
  error?: string;
  exists?: boolean;
  existing_url?: string;
}

export function PayrollAllocation() {
  const [result, setResult] = useState<PayrollAllocationResult | null>(null);
  const [allowUpdate, setAllowUpdate] = useState(false);

  const onSubmit: SubmitHandler<FormValues> = async (values) => {
    logger.debug(values);
  };

  const today = new Date();
  // Default to previous month for payroll allocation
  const previousMonth = new Date(today.getFullYear(), today.getMonth() - 1);
  const defaultMonth = {
    month: previousMonth.getMonth(),
    year: previousMonth.getFullYear(),
  };

  const {
    handleSubmit,
    errors,
    isSubmitting,
    isSubmitSuccessful,
    error,
    setValue,
    watch,
    setError,
    clearErrors,
  } = useFormHandler(onSubmit, {
    baseURL: API_BASE_URL,
    endpoint: API_ENDPOINTS.PAYROLL_ALLOCATION,
    formDataSubmission: true,
    defaultValues: {
      mp: defaultMonth,
      allow_update: "false",
    },
    onSuccess: (data: PayrollAllocationResult) => {
      setResult(data);
      // Reset allowUpdate checkbox after successful submission
      if (data.success) {
        setAllowUpdate(false);
        setValue("allow_update", "false");
      }
    },
  });

  const selectedMonth = watch("mp");
  const selectedFile = watch("file") as File | undefined;

  // Custom submit handler that validates file and syncs allowUpdate
  const onFormSubmit = (e: React.FormEvent) => {
    // Validate file before letting react-hook-form handle the rest
    if (!selectedFile) {
      e.preventDefault();
      setError("file", { type: "manual", message: "Please select a Gusto CSV file" });
      return;
    }
    // Sync allowUpdate state to form value
    setValue("allow_update", allowUpdate ? "true" : "false");
    // Clear previous result when re-submitting
    setResult(null);
    // Let react-hook-form handle the submission
  };

  // Handle allowUpdate checkbox change
  const handleAllowUpdateChange = (checked: boolean) => {
    setAllowUpdate(checked);
    setValue("allow_update", checked ? "true" : "false");
  };

  const isFutureMonth = (selected: typeof defaultMonth) => {
    const selectedDate = new Date(selected.year, selected.month);
    const firstOfCurrentMonth = new Date(today.getFullYear(), today.getMonth());
    return selectedDate >= firstOfCurrentMonth;
  };

  return (
    <form onSubmit={(e) => { onFormSubmit(e); if (selectedFile) handleSubmit(e); }}>
      <Feature
        title="Payroll Allocation"
        desc="Upload a Gusto 'Total By Location' CSV to create a labor journal entry in QuickBooks. This allocates payroll expenses from NOT SPECIFIED to individual stores."
        isLoading={isSubmitting}
        type="submit"
      >
        <JosiahAlert
          error={result?.exists ? undefined : error}
          isSuccess={isSubmitSuccessful && result?.success}
          successMessage={
            result?.journal_entry_url
              ? `Journal entry ${result.doc_number} created successfully!`
              : "Payroll allocation completed successfully!"
          }
        />

        {/* Show warning when entry already exists */}
        {result?.exists && result.existing_url && (
          <Alert variant="warning" className="mt-2">
            <AlertDescription>
              <div className="space-y-2">
                <p>
                  <strong>Journal entry {result.doc_number} already exists.</strong>
                </p>
                <p>
                  <a
                    href={result.existing_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    Review existing entry in QuickBooks
                  </a>
                </p>
                <label className="flex items-center gap-2 mt-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowUpdate}
                    onChange={(e) => handleAllowUpdateChange(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <span className="text-sm font-medium">
                    Replace existing entry (use with caution for closed months)
                  </span>
                </label>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Show link to QBO journal entry on success */}
        {isSubmitSuccessful && result?.success && result.journal_entry_url && (
          <Alert variant="default" className="mt-2 bg-green-50 border-green-200">
            <AlertDescription>
              <a
                href={result.journal_entry_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline font-medium"
              >
                Open {result.doc_number} in QuickBooks
              </a>
            </AlertDescription>
          </Alert>
        )}

        {/* Show warnings (e.g., reimbursements) */}
        {isSubmitSuccessful && result?.warnings && result.warnings.length > 0 && (
          <Alert variant="warning" className="mt-2">
            <AlertDescription>
              <strong>Manual Action Required:</strong>
              <ul className="list-disc list-inside mt-1">
                {result.warnings.map((warning, idx) => (
                  <li key={idx}>{warning.message}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Show summary on success */}
        {isSubmitSuccessful && result?.success && result.summary && (
          <Alert variant="default" className="mt-2">
            <AlertDescription>
              <strong>Summary:</strong>
              <ul className="list-disc list-inside mt-1">
                <li>Stores processed: {result.summary.stores_processed.join(", ")}</li>
                <li>Total gross earnings: ${result.summary.total_gross_earnings}</li>
                <li>Total employer taxes: ${result.summary.total_employer_taxes}</li>
              </ul>
            </AlertDescription>
          </Alert>
        )}

        <FormControl isInvalid={!!errors.mp}>
          <FormLabel>Select Month:</FormLabel>
          <MonthPicker
            value={selectedMonth}
            onChange={(value) => setValue("mp", value)}
            validate={{
              notFuture: (value) =>
                !isFutureMonth(value) || "Cannot select current or future month",
            }}
          />
          <FormMessage>{errors.mp && errors.mp.message}</FormMessage>
        </FormControl>

        {selectedMonth && isFutureMonth(selectedMonth) && (
          <Alert variant="destructive" className="mt-2">
            <AlertDescription>
              Please select a past month for payroll allocation.
            </AlertDescription>
          </Alert>
        )}

        <FormControl isInvalid={!!errors.file}>
          <FormLabel htmlFor="file">Select Gusto CSV:</FormLabel>
          <FileInput
            id="file"
            name="file"
            selectedFile={selectedFile}
            onFileChange={(file) => {
              if (file) {
                setValue("file", file);
                clearErrors("file");
              } else {
                setValue("file", undefined);
              }
            }}
            accept=".csv"
          />
          <FormMessage>{errors.file && errors.file.message}</FormMessage>
        </FormControl>

        <p className="text-sm text-gray-500 mt-2">
          Export the &quot;Total By Location&quot; report from Gusto for the selected month.
          The CSV should include employee work addresses to map to stores.
        </p>
      </Feature>
    </form>
  );
}
