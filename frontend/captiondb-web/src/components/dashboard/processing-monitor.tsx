"use client";

// ============================================================
// AI Processing Monitor
// ============================================================
// Reusable dashboard component that renders live AI processing
// jobs in an accessible table: status, start-time, ETA, progress
// and expandable per-job logs. Polls via useProcessingJobs while
// any job is active.
// ============================================================

import * as React from "react";
import {
  Ban,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Loader2,
  RotateCw,
  XCircle,
  type LucideIcon,
} from "lucide-react";

import { useProcessingJobs, isActiveJob } from "@/hooks/use-processing";
import type {
  ProcessingJobDTO,
  ProcessingJobStatus,
  ProcessingLogLevel,
} from "@/types/api";
import { cn } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeletons";
import { Button } from "@/components/ui/button";

// ─── Status presentation ──────────────────────────────────────────────────────

type BadgeVariant =
  | "default"
  | "secondary"
  | "muted"
  | "success"
  | "warning"
  | "destructive"
  | "outline";

const STATUS_META: Record<
  ProcessingJobStatus,
  { label: string; variant: BadgeVariant; icon: LucideIcon; spin?: boolean }
> = {
  QUEUED: { label: "Queued", variant: "muted", icon: Clock },
  RUNNING: { label: "Running", variant: "default", icon: Loader2, spin: true },
  RETRYING: { label: "Retrying", variant: "warning", icon: RotateCw, spin: true },
  COMPLETED: { label: "Completed", variant: "success", icon: CheckCircle2 },
  FAILED: { label: "Failed", variant: "destructive", icon: XCircle },
  CANCELLED: { label: "Cancelled", variant: "muted", icon: Ban },
};

function StatusBadge({ status }: { status: ProcessingJobStatus }) {
  const meta = STATUS_META[status];
  const Icon = meta.icon;
  return (
    <Badge variant={meta.variant}>
      <Icon className={cn(meta.spin && "animate-spin")} aria-hidden="true" />
      {meta.label}
    </Badge>
  );
}

const LOG_LEVEL_CLASS: Record<ProcessingLogLevel, string> = {
  debug: "text-muted-foreground",
  info: "text-foreground",
  warning: "text-amber-600 dark:text-amber-400",
  error: "text-destructive",
};

// ─── Formatting helpers ───────────────────────────────────────────────────────

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDurationSeconds(totalSeconds: number): string {
  const s = Math.max(0, Math.round(totalSeconds));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  if (m < 60) return rem ? `${m}m ${rem}s` : `${m}m`;
  const h = Math.floor(m / 60);
  const remMin = m % 60;
  return remMin ? `${h}h ${remMin}m` : `${h}h`;
}

/**
 * Estimated time remaining. Prefers a backend-provided ETA; otherwise
 * extrapolates from elapsed time and current progress.
 */
function formatEta(job: ProcessingJobDTO): string {
  if (!isActiveJob(job.status)) return "—";

  if (job.estimated_completion_at) {
    const remaining =
      (new Date(job.estimated_completion_at).getTime() - Date.now()) / 1000;
    if (Number.isFinite(remaining)) {
      return remaining <= 0 ? "Any moment" : `~${formatDurationSeconds(remaining)}`;
    }
  }

  if (job.started_at && job.progress > 0 && job.progress < 100) {
    const elapsed = (Date.now() - new Date(job.started_at).getTime()) / 1000;
    if (elapsed > 0) {
      const estimatedTotal = elapsed / (job.progress / 100);
      const remaining = estimatedTotal - elapsed;
      return remaining <= 0 ? "Any moment" : `~${formatDurationSeconds(remaining)}`;
    }
  }

  return "Calculating…";
}

function clampPercent(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, Math.round(value)));
}

function jobLabel(job: ProcessingJobDTO): string {
  return job.project_name || job.project_id || job.task_id;
}

// ─── Expandable detail row ────────────────────────────────────────────────────

function JobDetails({ job }: { job: ProcessingJobDTO }) {
  const logs = job.logs ?? [];
  return (
    <div className="space-y-3 bg-muted/30 px-4 py-3 text-sm">
      <dl className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
        <div className="flex gap-2">
          <dt className="text-muted-foreground">Task ID</dt>
          <dd className="font-mono text-xs break-all">{job.task_id}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="text-muted-foreground">Last update</dt>
          <dd>{formatTimestamp(job.updated_at)}</dd>
        </div>
        {job.completed_at && (
          <div className="flex gap-2">
            <dt className="text-muted-foreground">Completed</dt>
            <dd>{formatTimestamp(job.completed_at)}</dd>
          </div>
        )}
        {job.retry_count > 0 && (
          <div className="flex gap-2">
            <dt className="text-muted-foreground">Retries</dt>
            <dd>{job.retry_count}</dd>
          </div>
        )}
      </dl>

      {job.error_message && (
        <p className="rounded-md border border-destructive/20 bg-destructive/10 px-3 py-2 text-destructive">
          {job.error_message}
        </p>
      )}

      <div>
        <p className="mb-1 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
          Logs
        </p>
        {logs.length === 0 ? (
          <p className="text-xs text-muted-foreground">No logs available.</p>
        ) : (
          <ul className="max-h-48 space-y-0.5 overflow-y-auto rounded-md bg-background/60 p-2 font-mono text-xs">
            {logs.map((log, i) => (
              <li key={`${log.timestamp}-${i}`} className="flex gap-2">
                <span className="shrink-0 text-muted-foreground tabular-nums">
                  {formatTimestamp(log.timestamp)}
                </span>
                <span className={cn("break-words", LOG_LEVEL_CLASS[log.level])}>
                  {log.message}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

// ─── Table row ────────────────────────────────────────────────────────────────

const COLUMN_COUNT = 6;

function JobRow({ job }: { job: ProcessingJobDTO }) {
  const [expanded, setExpanded] = React.useState(false);
  const pct = clampPercent(job.progress);
  const label = jobLabel(job);

  return (
    <>
      <TableRow>
        <TableCell className="w-8 pr-0">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-expanded={expanded}
            aria-label={expanded ? `Hide details for ${label}` : `Show details for ${label}`}
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? (
              <ChevronDown aria-hidden="true" />
            ) : (
              <ChevronRight aria-hidden="true" />
            )}
          </Button>
        </TableCell>
        <TableCell>
          <div className="font-medium">{label}</div>
          {job.current_stage && (
            <div className="text-xs text-muted-foreground">{job.current_stage}</div>
          )}
        </TableCell>
        <TableCell>
          <StatusBadge status={job.status} />
        </TableCell>
        <TableCell className="text-muted-foreground tabular-nums">
          {formatTimestamp(job.started_at)}
        </TableCell>
        <TableCell className="text-muted-foreground tabular-nums">
          {formatEta(job)}
        </TableCell>
        <TableCell className="min-w-[8rem]">
          <div className="flex items-center gap-2">
            <Progress
              value={pct}
              aria-label={`${label} progress`}
              className="w-full"
            />
            <span className="w-9 shrink-0 text-right text-xs text-muted-foreground tabular-nums">
              {pct}%
            </span>
          </div>
        </TableCell>
      </TableRow>
      {expanded && (
        <TableRow className="hover:bg-transparent">
          <TableCell colSpan={COLUMN_COUNT} className="p-0">
            <JobDetails job={job} />
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

export function ProcessingMonitorSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-64" />
      </CardHeader>
      <CardContent className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-4 w-40 flex-1" />
            <Skeleton className="h-5 w-20 rounded-full" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-2 w-32" />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// ─── Public component ─────────────────────────────────────────────────────────

export interface ProcessingMonitorProps {
  /** Optional heading override. */
  title?: string;
  description?: string;
  /** Filter to a single status (e.g. only running jobs). */
  status?: ProcessingJobStatus;
  /** Max jobs to request. */
  limit?: number;
  className?: string;
}

export function ProcessingMonitor({
  title = "AI Processing Monitor",
  description = "Live status of AI processing jobs.",
  status,
  limit = 50,
  className,
}: ProcessingMonitorProps) {
  const { data, isLoading, isError, refetch } = useProcessingJobs({
    status,
    limit,
  });

  if (isLoading) {
    return <ProcessingMonitorSkeleton />;
  }

  const jobs = data?.data ?? [];

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {isError ? (
          <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-destructive/20 bg-destructive/10 p-8 text-center text-destructive">
            <p className="text-sm font-medium">Unable to load processing jobs.</p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        ) : jobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center">
            <h3 className="font-semibold">No active jobs</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              AI processing jobs will appear here as they run.
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8">
                  <span className="sr-only">Expand</span>
                </TableHead>
                <TableHead>Job</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>ETA</TableHead>
                <TableHead>Progress</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.map((job) => (
                <JobRow key={job.task_id} job={job} />
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
