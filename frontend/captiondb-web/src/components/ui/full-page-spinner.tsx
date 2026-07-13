// ============================================================
// Full-Page Spinner
// ============================================================

import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface FullPageSpinnerProps {
  className?: string;
  message?: string;
}

export function FullPageSpinner({ className, message }: FullPageSpinnerProps) {
  return (
    <div
      className={cn(
        "flex min-h-screen flex-col items-center justify-center gap-4 bg-background",
        className
      )}
    >
      <Loader2 className="h-10 w-10 animate-spin text-primary" />
      {message && (
        <p className="text-sm text-muted-foreground animate-pulse">{message}</p>
      )}
    </div>
  );
}

// ─── Inline spinner ──────────────────────────────────────────────────────────

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeMap = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-8 w-8",
};

export function Spinner({ size = "md", className }: SpinnerProps) {
  return (
    <Loader2
      className={cn("animate-spin text-current", sizeMap[size], className)}
    />
  );
}
