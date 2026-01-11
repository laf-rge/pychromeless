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
import { Alert, AlertDescription } from "../../components/ui/alert";
import { API_BASE_URL, API_ENDPOINTS } from "../../config/api";

interface DepositInfo {
  store: string;
  date: string;
  amount: string;
  reason?: string;
  error?: string;
}

interface GrubhubImportResult {
  success: boolean;
  summary: {
    total_deposits: number;
    imported: number;
    skipped: number;
    failed: number;
  };
  imported_deposits: DepositInfo[];
  skipped_deposits: DepositInfo[];
  errors: DepositInfo[];
}

export function GrubhubImport() {
  const [result, setResult] = useState<GrubhubImportResult | null>(null);
  const [processAllDates, setProcessAllDates] = useState(true);

  const onSubmit: SubmitHandler<FormValues> = async (values) => {
    logger.debug(values);
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
    endpoint: API_ENDPOINTS.GRUBHUB_CSV_IMPORT,
    formDataSubmission: true,
    defaultValues: {
      start_date: "",
      end_date: "",
    },
    onSuccess: (data: GrubhubImportResult) => {
      setResult(data);
    },
  });

  const selectedFile = watch("file") as File | undefined;
  const startDate = watch("start_date") as string;
  const endDate = watch("end_date") as string;

  // Custom submit handler that validates file
  const onFormSubmit = (e: React.FormEvent) => {
    if (!selectedFile) {
      e.preventDefault();
      setError("file", { type: "manual", message: "Please select a GrubHub CSV file" });
      return;
    }
    // Clear dates if processing all
    if (processAllDates) {
      setValue("start_date", "");
      setValue("end_date", "");
    }
    // Clear previous result when re-submitting
    setResult(null);
  };

  return (
    <form onSubmit={(e) => { onFormSubmit(e); if (selectedFile) handleSubmit(e); }}>
      <Feature
        title="GrubHub CSV Import"
        desc="Upload a GrubHub deposit CSV export to create deposit transactions in QuickBooks. Duplicate deposits are automatically skipped."
        isLoading={isSubmitting}
        type="submit"
      >
        <JosiahAlert
          error={error}
          isSuccess={isSubmitSuccessful && result?.success}
          successMessage={
            result
              ? `Imported ${result.summary.imported} deposits, skipped ${result.summary.skipped} duplicates`
              : "Import completed successfully!"
          }
        />

        {/* Show summary on completion */}
        {isSubmitSuccessful && result && (
          <Alert variant={result.summary.failed > 0 ? "warning" : "default"} className="mt-2 bg-green-50 border-green-200">
            <AlertDescription>
              <strong>Import Summary:</strong>
              <ul className="list-disc list-inside mt-1">
                <li>Total deposits in file: {result.summary.total_deposits}</li>
                <li className="text-green-600">Successfully imported: {result.summary.imported}</li>
                <li className="text-yellow-600">Skipped (already exist): {result.summary.skipped}</li>
                {result.summary.failed > 0 && (
                  <li className="text-red-600">Failed: {result.summary.failed}</li>
                )}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Show imported deposits */}
        {isSubmitSuccessful && result && result.imported_deposits.length > 0 && (
          <Alert variant="default" className="mt-2">
            <AlertDescription>
              <details>
                <summary className="cursor-pointer font-medium">
                  Imported Deposits ({result.imported_deposits.length})
                </summary>
                <ul className="list-disc list-inside mt-2 text-sm">
                  {result.imported_deposits.map((deposit, idx) => (
                    <li key={idx}>
                      Store {deposit.store} - {deposit.date} - ${deposit.amount}
                    </li>
                  ))}
                </ul>
              </details>
            </AlertDescription>
          </Alert>
        )}

        {/* Show skipped deposits */}
        {isSubmitSuccessful && result && result.skipped_deposits.length > 0 && (
          <Alert variant="warning" className="mt-2">
            <AlertDescription>
              <details>
                <summary className="cursor-pointer font-medium">
                  Skipped Deposits ({result.skipped_deposits.length})
                </summary>
                <ul className="list-disc list-inside mt-2 text-sm">
                  {result.skipped_deposits.map((deposit, idx) => (
                    <li key={idx}>
                      Store {deposit.store} - {deposit.date} - ${deposit.amount} ({deposit.reason})
                    </li>
                  ))}
                </ul>
              </details>
            </AlertDescription>
          </Alert>
        )}

        {/* Show errors */}
        {isSubmitSuccessful && result && result.errors.length > 0 && (
          <Alert variant="destructive" className="mt-2">
            <AlertDescription>
              <strong>Failed Deposits:</strong>
              <ul className="list-disc list-inside mt-1 text-sm">
                {result.errors.map((deposit, idx) => (
                  <li key={idx}>
                    Store {deposit.store} - {deposit.date} - ${deposit.amount}: {deposit.error}
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        <FormControl isInvalid={!!errors.file}>
          <FormLabel htmlFor="file">Select GrubHub CSV:</FormLabel>
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

        <div className="mt-4 space-y-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={processAllDates}
              onChange={(e) => setProcessAllDates(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <span className="text-sm font-medium">
              Process all dates in file (recommended)
            </span>
          </label>

          {!processAllDates && (
            <div className="flex gap-4">
              <FormControl isInvalid={!!errors.start_date} className="flex-1">
                <FormLabel htmlFor="start_date">Start Date:</FormLabel>
                <input
                  type="date"
                  id="start_date"
                  value={startDate || ""}
                  onChange={(e) => setValue("start_date", e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
                <FormMessage>{errors.start_date && errors.start_date.message}</FormMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.end_date} className="flex-1">
                <FormLabel htmlFor="end_date">End Date:</FormLabel>
                <input
                  type="date"
                  id="end_date"
                  value={endDate || ""}
                  onChange={(e) => setValue("end_date", e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
                <FormMessage>{errors.end_date && errors.end_date.message}</FormMessage>
              </FormControl>
            </div>
          )}
        </div>

        <p className="text-sm text-gray-500 mt-4">
          Export the deposit report from GrubHub for Restaurants portal.
          Duplicate deposits (same date, store, and amount) will be automatically skipped.
        </p>
      </Feature>
    </form>
  );
}
