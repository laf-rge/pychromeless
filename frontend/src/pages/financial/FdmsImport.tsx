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

interface FdmsResult {
  filename: string;
  store: string | null;
  statement_month: string | null;
  total_fees: string | null;
  bill_url: string | null;
  bill_doc_number: string | null;
  has_chargebacks: boolean;
  has_adjustments: boolean;
  chargebacks_text: string | null;
  adjustments_text: string | null;
  error: string | null;
}

interface FdmsImportResult {
  success: boolean;
  summary: {
    total_files: number;
    bills_created: number;
    files_with_chargebacks: number;
    failed: number;
  };
  results: FdmsResult[];
}

export function FdmsImport() {
  const [result, setResult] = useState<FdmsImportResult | null>(null);

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
    endpoint: API_ENDPOINTS.FDMS_STATEMENT_IMPORT,
    formDataSubmission: true,
    defaultValues: {},
    onSuccess: (data: FdmsImportResult) => {
      setResult(data);
    },
  });

  const selectedFiles = watch("files") as File[] | undefined;

  // Reasonable limits for upload
  const MAX_FILES = 10;
  const MAX_FILE_SIZE_MB = 5;
  const MAX_TOTAL_SIZE_MB = 25;

  const onFormSubmit = (e: React.FormEvent) => {
    if (!selectedFiles || selectedFiles.length === 0) {
      e.preventDefault();
      setError("files", { type: "manual", message: "Please select at least one FDMS statement PDF" });
      return;
    }

    if (selectedFiles.length > MAX_FILES) {
      e.preventDefault();
      setError("files", { type: "manual", message: `Maximum ${MAX_FILES} files allowed per upload` });
      return;
    }

    // Check individual file sizes and total
    const totalSize = selectedFiles.reduce((sum, f) => sum + f.size, 0);
    const oversizedFile = selectedFiles.find(f => f.size > MAX_FILE_SIZE_MB * 1024 * 1024);

    if (oversizedFile) {
      e.preventDefault();
      setError("files", { type: "manual", message: `File "${oversizedFile.name}" exceeds ${MAX_FILE_SIZE_MB}MB limit` });
      return;
    }

    if (totalSize > MAX_TOTAL_SIZE_MB * 1024 * 1024) {
      e.preventDefault();
      setError("files", { type: "manual", message: `Total file size exceeds ${MAX_TOTAL_SIZE_MB}MB limit` });
      return;
    }

    setResult(null);
  };

  const successfulResults = result?.results.filter(r => !r.error) || [];
  const failedResults = result?.results.filter(r => r.error) || [];
  const chargebackResults = result?.results.filter(r => r.has_chargebacks || r.has_adjustments) || [];

  return (
    <form onSubmit={(e) => { onFormSubmit(e); if (selectedFiles && selectedFiles.length > 0) handleSubmit(e); }}>
      <Feature
        title="FDMS Statement Import"
        desc="Upload FDMS credit card processor statement PDFs to create bills in QuickBooks. Each statement generates a bill with fee line items. Chargebacks and adjustments are flagged for review."
        isLoading={isSubmitting}
        type="submit"
      >
        <JosiahAlert
          error={error}
          isSuccess={isSubmitSuccessful && result?.success}
          successMessage={
            result
              ? `Created ${result.summary.bills_created} bills from ${result.summary.total_files} files`
              : "Import completed successfully!"
          }
        />

        {isSubmitSuccessful && result && (
          <Alert variant={result.summary.failed > 0 ? "warning" : "default"} className="mt-2 bg-green-50 border-green-200">
            <AlertDescription>
              <strong>Import Summary:</strong>
              <ul className="list-disc list-inside mt-1">
                <li>Total files: {result.summary.total_files}</li>
                <li className="text-green-600">Bills created: {result.summary.bills_created}</li>
                {result.summary.files_with_chargebacks > 0 && (
                  <li className="text-yellow-600">Files with chargebacks/adjustments: {result.summary.files_with_chargebacks}</li>
                )}
                {result.summary.failed > 0 && (
                  <li className="text-red-600">Failed: {result.summary.failed}</li>
                )}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {isSubmitSuccessful && successfulResults.length > 0 && (
          <Alert variant="default" className="mt-2">
            <AlertDescription>
              <details>
                <summary className="cursor-pointer font-medium">
                  Created Bills ({successfulResults.length})
                </summary>
                <ul className="list-disc list-inside mt-2 text-sm space-y-1">
                  {successfulResults.map((r, idx) => (
                    <li key={idx}>
                      Store {r.store} - {r.statement_month} - {r.total_fees}
                      {r.bill_url && (
                        <a
                          href={r.bill_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-2 text-blue-600 hover:underline"
                        >
                          View Bill
                        </a>
                      )}
                      {(r.has_chargebacks || r.has_adjustments) && (
                        <span className="ml-2 text-yellow-600">
                          (has {r.has_chargebacks && "chargebacks"}{r.has_chargebacks && r.has_adjustments && "/"}{r.has_adjustments && "adjustments"})
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              </details>
            </AlertDescription>
          </Alert>
        )}

        {isSubmitSuccessful && chargebackResults.length > 0 && (
          <Alert variant="warning" className="mt-2">
            <AlertDescription>
              <details open>
                <summary className="cursor-pointer font-medium">
                  Chargebacks/Adjustments Found ({chargebackResults.length})
                </summary>
                <div className="mt-2 text-sm space-y-3">
                  {chargebackResults.map((r, idx) => (
                    <div key={idx} className="border-l-2 border-yellow-400 pl-3">
                      <div className="font-medium">Store {r.store} - {r.statement_month}</div>
                      {r.chargebacks_text && (
                        <pre className="text-xs mt-1 whitespace-pre-wrap text-red-700">{r.chargebacks_text}</pre>
                      )}
                      {r.adjustments_text && (
                        <pre className="text-xs mt-1 whitespace-pre-wrap text-orange-700">{r.adjustments_text}</pre>
                      )}
                    </div>
                  ))}
                </div>
              </details>
            </AlertDescription>
          </Alert>
        )}

        {isSubmitSuccessful && failedResults.length > 0 && (
          <Alert variant="destructive" className="mt-2">
            <AlertDescription>
              <strong>Failed Files:</strong>
              <ul className="list-disc list-inside mt-1 text-sm">
                {failedResults.map((r, idx) => (
                  <li key={idx}>
                    {r.filename}: {r.error}
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        <FormControl isInvalid={!!errors.files}>
          <FormLabel htmlFor="files">Select FDMS Statement PDFs:</FormLabel>
          <FileInput
            id="files"
            name="files"
            multiple
            selectedFiles={selectedFiles}
            onFilesChange={(files) => {
              if (files && files.length > 0) {
                setValue("files", files);
                clearErrors("files");
              } else {
                setValue("files", undefined);
              }
            }}
            accept=".pdf"
          />
          <FormMessage>{errors.files && (errors.files as { message?: string }).message}</FormMessage>
        </FormControl>

        <p className="text-sm text-gray-500 mt-4">
          Upload monthly FDMS statement PDFs. Bills will be created with the statement period end date
          and line items for Interchange/Program Fees, Service Charges, and Fees.
          Chargebacks and adjustments will be noted on the bill and displayed here for review.
        </p>
      </Feature>
    </form>
  );
}
