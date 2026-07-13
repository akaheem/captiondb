import * as React from "react";

import { cn } from "@/lib/utils";

/** Consistent "Not available" marker for fields the backend does not expose. */
export function NotAvailable({ className }: { className?: string }) {
  return (
    <span className={cn("text-sm text-muted-foreground italic", className)}>
      Not available
    </span>
  );
}

/**
 * A labelled field that renders its value, an empty-list fallback, or the
 * "Not available" marker when the value is absent. Never throws on missing data.
 */
export function Field({
  label,
  value,
  children,
}: {
  label: string;
  value?: unknown;
  children?: React.ReactNode;
}) {
  const hasChildren = children !== undefined && children !== null;
  const isEmpty =
    !hasChildren &&
    (value === undefined ||
      value === null ||
      (typeof value === "string" && value.trim() === "") ||
      (Array.isArray(value) && value.length === 0));

  return (
    <div className="space-y-1">
      <dt className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        {label}
      </dt>
      <dd className="text-sm text-foreground">
        {hasChildren ? children : isEmpty ? <NotAvailable /> : String(value)}
      </dd>
    </div>
  );
}

/** Renders a list of short strings as pill tags, or "Not available". */
export function TagList({ items }: { items?: string[] | null }) {
  if (!items || items.length === 0) return <NotAvailable />;
  return (
    <ul className="flex flex-wrap gap-1.5">
      {items.map((item, i) => (
        <li
          key={`${item}-${i}`}
          className="rounded-full bg-muted px-2 py-0.5 text-xs text-foreground"
        >
          {item}
        </li>
      ))}
    </ul>
  );
}
