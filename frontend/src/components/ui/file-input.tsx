import * as React from "react";
import { cn } from "../../utils/cn";
import { Button } from "./button";

export interface FileInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type" | "value"> {
  onFileChange?: (file: File | undefined) => void;
  selectedFile?: File;
}

const FileInput = React.forwardRef<HTMLInputElement, FileInputProps>(
  ({ className, onFileChange, selectedFile, id, onChange, ...props }, ref) => {
    const inputRef = React.useRef<HTMLInputElement>(null);

    // Merge refs
    React.useImperativeHandle(ref, () => inputRef.current as HTMLInputElement);

    const handleClick = () => {
      inputRef.current?.click();
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      onFileChange?.(file);
      onChange?.(e);
    };

    return (
      <div className={cn("flex items-center gap-3", className)}>
        <input
          type="file"
          ref={inputRef}
          className="sr-only"
          id={id}
          {...props}
          onChange={handleChange}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleClick}
          className="shrink-0"
        >
          Choose File
        </Button>
        <span
          className={cn(
            "text-sm truncate",
            selectedFile ? "text-foreground" : "text-muted-foreground"
          )}
        >
          {selectedFile ? selectedFile.name : "No file selected"}
        </span>
      </div>
    );
  }
);
FileInput.displayName = "FileInput";

export { FileInput };
