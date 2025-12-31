import React from "react";
import { Button } from "../../components/ui/button";
import { Feature } from "../../components/features/Feature";
import { JosiahAlert } from "../../components/features/JosiahAlert";
import { AxiosError, InternalAxiosRequestConfig } from "axios";

export function ErrorTester() {
  const [error, setError] = React.useState<AxiosError>();

  const createError = (status: number, message: string) => {
    return new AxiosError(
      message,
      "TEST_ERROR",
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      { headers: {} } as any,
      {},
      {
        status,
        statusText: "Test Error",
        headers: {},
        data: {},
        config: { headers: {} } as InternalAxiosRequestConfig,
      }
    );
  };

  const testErrors = [
    { status: 401, message: "Unauthorized: Session expired" },
    { status: 404, message: "Not Found: Resource doesn't exist" },
    { status: 500, message: "Internal Server Error: Something went wrong" },
    {
      status: 503,
      message: "Service Unavailable: System is down for maintenance",
    },
  ];

  if (!import.meta.env.DEV) {
    return null;
  }

  return (
    <Feature
      title="Error Tester (Dev Only)"
      desc="Test different error states for Josiah components."
    >
      <JosiahAlert error={error} successMessage="" />
      <div className="space-y-4 p-4 border rounded-md">
        <p className="font-bold">Test Error States:</p>
        {testErrors.map((testError) => (
          <Button
            key={testError.status}
            onClick={() =>
              setError(createError(testError.status, testError.message))
            }
            variant="outline"
            size="sm"
            className="w-full"
          >
            Test {testError.status} Error
          </Button>
        ))}
        <Button
          onClick={() => setError(undefined)}
          variant="default"
          size="sm"
          className="w-full"
        >
          Clear Error
        </Button>
      </div>
    </Feature>
  );
}
