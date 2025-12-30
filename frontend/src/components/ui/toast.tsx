import * as React from "react";
import { Alert, AlertTitle, AlertDescription } from "./alert";

export interface ToastProps {
  title?: string;
  description: string;
  variant?: "default" | "destructive" | "success" | "warning";
  duration?: number;
  onClose?: () => void;
}

export function Toast({
  title,
  description,
  variant = "default",
  duration = 3000,
  onClose,
}: ToastProps) {
  React.useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose?.();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  return (
    <Alert variant={variant} className="min-w-[350px]">
      {title && <AlertTitle>{title}</AlertTitle>}
      <AlertDescription>{description}</AlertDescription>
    </Alert>
  );
}
