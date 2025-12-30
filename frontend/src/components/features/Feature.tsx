import { ReactNode } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "../ui/card";
import { Button, ButtonProps } from "../ui/button";
import { cn } from "../../utils/cn";

export interface FeatureProps extends ButtonProps {
  title: string;
  desc: string;
  children?: ReactNode;
  buttonText?: string;
  isLoading?: boolean;
}

export function Feature({
  title,
  desc,
  children,
  buttonText = "Submit",
  isLoading,
  className,
  disabled,
  ...rest
}: FeatureProps) {
  return (
    <Card className={cn("w-full max-w-md", className)}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{desc}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">{children}</CardContent>
      <CardFooter>
        <Button variant="outline" className="w-full" disabled={isLoading || disabled} {...rest}>
          {isLoading ? "Loading..." : buttonText}
        </Button>
      </CardFooter>
    </Card>
  );
}
