import { Component, ErrorInfo, ReactNode } from "react";
import { Button } from "./ui/button";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { logger } from "../utils/logger";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    logger.error("Error caught by boundary:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  public render() {
    if (this.state.hasError) {
      // Only show error in dev mode
      if (!import.meta.env.DEV) {
        return (
          <div className="flex min-h-screen items-center justify-center p-4">
            <Card className="max-w-md">
              <CardHeader>
                <CardTitle>Something went wrong</CardTitle>
              </CardHeader>
              <CardContent>
                <Alert variant="destructive">
                  <AlertDescription>
                    An unexpected error occurred. Please refresh the page.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </div>
        );
      }

      return (
        <div className="p-4">
          <Card className="mb-4">
            <CardHeader>
              <CardTitle>Something went wrong!</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert variant="destructive">
                <AlertTitle>Error Details</AlertTitle>
                <AlertDescription className="mt-2 font-mono text-xs break-all">
                  {this.state.error?.message}
                </AlertDescription>
              </Alert>
              <Button onClick={this.handleReset} variant="default">
                Try Again
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
