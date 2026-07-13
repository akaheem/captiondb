"use client";

import { ArrowLeft } from "lucide-react";

/** Client-only "go back" control for use inside server-rendered pages. */
export function BackButton() {
  return (
    <button
      onClick={() => history.back()}
      className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-5 py-2.5 text-sm font-semibold text-foreground shadow-sm transition-colors hover:bg-muted"
    >
      <ArrowLeft className="h-4 w-4" />
      Go back
    </button>
  );
}
