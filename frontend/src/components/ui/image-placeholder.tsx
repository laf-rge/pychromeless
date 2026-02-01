import { cn } from "../../utils/cn";

type PlaceholderVariant = "food" | "store" | "team" | "generic";
type AspectRatio = "16/9" | "4/3" | "1/1" | "3/4";

interface ImagePlaceholderProps {
  variant?: PlaceholderVariant;
  aspectRatio?: AspectRatio;
  className?: string;
  label?: string;
}

function PlaceholderIcon({ variant }: { variant: PlaceholderVariant }) {
  const iconClass = "w-10 h-10 text-[#C4B8A8]";

  switch (variant) {
    case "food":
      return (
        <svg className={iconClass} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          {/* Fork */}
          <path d="M14 8v8c0 2.2 1.8 4 4 4v20" />
          <path d="M14 8v8" />
          <path d="M18 8v8" />
          <path d="M10 8v8c0 2.2 1.8 4 4 4" />
          {/* Knife */}
          <path d="M34 8v32" />
          <path d="M34 8c-3 0-6 4-6 10s3 6 6 6" />
        </svg>
      );
    case "store":
      return (
        <svg className={iconClass} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 40h36" />
          <path d="M10 40V22" />
          <path d="M38 40V22" />
          <path d="M6 20l6-12h24l6 12" />
          <path d="M6 20c0 2.2 1.8 4 4 4s4-1.8 4-4" />
          <path d="M14 20c0 2.2 1.8 4 4 4s4-1.8 4-4" />
          <path d="M22 20c0 2.2 1.8 4 4 4s4-1.8 4-4" />
          <path d="M30 20c0 2.2 1.8 4 4 4s4-1.8 4-4" />
          <rect x="18" y="30" width="12" height="10" />
        </svg>
      );
    case "team":
      return (
        <svg className={iconClass} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="24" cy="16" r="6" />
          <path d="M12 40c0-6.6 5.4-12 12-12s12 5.4 12 12" />
          <circle cx="38" cy="14" r="4" />
          <path d="M42 34c0-4-2.7-7.4-6.4-8.4" />
          <circle cx="10" cy="14" r="4" />
          <path d="M6 34c0-4 2.7-7.4 6.4-8.4" />
        </svg>
      );
    default:
      return (
        <svg className={iconClass} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <rect x="6" y="10" width="36" height="28" rx="2" />
          <circle cx="18" cy="22" r="4" />
          <path d="M42 32l-10-10-8 8-4-4-14 14" />
        </svg>
      );
  }
}

export function ImagePlaceholder({
  variant = "generic",
  aspectRatio = "16/9",
  className,
  label,
}: ImagePlaceholderProps) {
  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center overflow-hidden rounded-lg border-2 border-dashed border-[#E8E2D6] bg-[#F5F0E8]",
        className
      )}
      style={{ aspectRatio }}
    >
      <PlaceholderIcon variant={variant} />
      {label && (
        <p className="mt-2 text-xs font-heading text-[#B8AFA0]">{label}</p>
      )}
    </div>
  );
}
