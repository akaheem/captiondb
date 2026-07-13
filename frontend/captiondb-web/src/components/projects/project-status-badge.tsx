import { Badge } from "@/components/ui/badge";
import type { VideoStatus } from "@/types/api";

const STATUS_CONFIG: Record<
  VideoStatus,
  { label: string; variant: "muted" | "warning" | "success" | "destructive" }
> = {
  PENDING: { label: "Pending", variant: "muted" },
  PROCESSING: { label: "Processing", variant: "warning" },
  COMPLETED: { label: "Completed", variant: "success" },
  FAILED: { label: "Failed", variant: "destructive" },
};

/** Colored status pill for a project/video status. */
export function ProjectStatusBadge({ status }: { status: VideoStatus }) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    variant: "muted" as const,
  };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
