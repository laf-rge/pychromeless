import * as React from "react";
import { cn } from "../../utils/cn";
import { Button } from "./button";

export interface FileInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type" | "value"> {
  onFileChange?: (file: File | undefined) => void;
  onFilesChange?: (files: File[]) => void;
  selectedFile?: File;
  selectedFiles?: File[];
}

const FileInput = React.forwardRef<HTMLInputElement, FileInputProps>(
  ({ className, onFileChange, onFilesChange, selectedFile, selectedFiles, id, onChange, multiple, ...props }, ref) => {
    const inputRef = React.useRef<HTMLInputElement>(null);

    // Merge refs
    React.useImperativeHandle(ref, () => inputRef.current as HTMLInputElement);

    const handleClick = () => {
      inputRef.current?.click();
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      if (multiple) {
        const files = e.target.files ? Array.from(e.target.files) : [];
        onFilesChange?.(files);
      } else {
        const file = e.target.files?.[0];
        onFileChange?.(file);
      }
      onChange?.(e);
    };

    const getDisplayText = () => {
      if (multiple && selectedFiles) {
        if (selectedFiles.length === 0) {
          return "No files selected";
        }
        if (selectedFiles.length === 1) {
          return selectedFiles[0].name;
        }
        return `${selectedFiles.length} files selected`;
      }
      return selectedFile ? selectedFile.name : "No file selected";
    };

    const hasSelection = multiple ? (selectedFiles && selectedFiles.length > 0) : !!selectedFile;

    return (
      <div className={cn("flex items-center gap-3", className)}>
        <input
          type="file"
          ref={inputRef}
          className="sr-only"
          id={id}
          multiple={multiple}
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
          {multiple ? "Choose Files" : "Choose File"}
        </Button>
        <span
          className={cn(
            "text-sm truncate",
            hasSelection ? "text-foreground" : "text-muted-foreground"
          )}
        >
          {getDisplayText()}
        </span>
      </div>
    );
  }
);
FileInput.displayName = "FileInput";

export { FileInput };
