import { AxiosError } from "axios";
import { Alert, AlertTitle, AlertDescription } from "../ui/alert";

interface JosiahAlertProps {
  error?: AxiosError;
  isSuccess?: boolean;
  successMessage: string;
}

export function JosiahAlert({
  error,
  isSuccess,
  successMessage,
}: JosiahAlertProps) {
  if (error) {
    const errorMessage =
      error.response?.status === 401
        ? "Your session has expired. Please refresh the page and try again."
        : error.response?.status === 404
        ? "The requested resource was not found."
        : error.response?.status === 500
        ? "An internal server error occurred. Please try again later."
        : error.message;

    return (
      <Alert variant="destructive" className="mb-4">
        <AlertTitle>Josiah Error!</AlertTitle>
        <AlertDescription>{errorMessage}</AlertDescription>
      </Alert>
    );
  }

  if (isSuccess) {
    return (
      <Alert variant="success" className="mb-4">
        <AlertTitle>Josiah is on it!</AlertTitle>
        <AlertDescription>{successMessage}</AlertDescription>
      </Alert>
    );
  }

  return null;
}
