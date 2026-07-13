// ============================================================
// AI Processing Monitor — React Query hooks
// ============================================================
// Live status of AI processing jobs. These poll while work is
// in-flight so the monitor UI updates without a manual refresh.
// ============================================================

import { useQuery } from "@tanstack/react-query";
import { processingService } from "@/services/processing.service";
import { queryKeys } from "@/lib/query-keys";
import type {
  ProcessingJobDTO,
  ProcessingJobListResponse,
  ProcessingJobStatus,
} from "@/types/api";

/** Statuses that represent still-running work worth polling for. */
const ACTIVE_STATUSES: ReadonlySet<ProcessingJobStatus> = new Set([
  "QUEUED",
  "RUNNING",
  "RETRYING",
]);

export function isActiveJob(status: ProcessingJobStatus): boolean {
  return ACTIVE_STATUSES.has(status);
}

interface UseProcessingJobsOptions {
  /** Filter to a single status (e.g. "RUNNING"). */
  status?: ProcessingJobStatus;
  limit?: number;
  offset?: number;
  /** Poll interval (ms) while any job is active. Defaults to 5s. */
  refetchIntervalMs?: number;
  enabled?: boolean;
}

/**
 * List AI processing jobs. Polls automatically while at least one job is
 * still active, and stops polling once everything has settled.
 */
export function useProcessingJobs(options: UseProcessingJobsOptions = {}) {
  const {
    status,
    limit = 50,
    offset = 0,
    refetchIntervalMs = 5_000,
    enabled = true,
  } = options;

  const filters = { status, limit, offset };

  return useQuery<ProcessingJobListResponse>({
    queryKey: queryKeys.processing.jobs(filters),
    queryFn: () => processingService.listJobs(filters),
    enabled,
    refetchInterval: (query) => {
      const jobs = query.state.data?.data ?? [];
      return jobs.some((job) => isActiveJob(job.status))
        ? refetchIntervalMs
        : false;
    },
  });
}

interface UseJobStatusOptions {
  /** Poll interval (ms) while the job is active. Defaults to 2s. */
  refetchIntervalMs?: number;
  enabled?: boolean;
}

/**
 * Live status for a single job, including progress and recent logs.
 * Polls quickly while the job is active, then stops once it settles.
 */
export function useJobStatus(
  jobId: string | null | undefined,
  options: UseJobStatusOptions = {}
) {
  const { refetchIntervalMs = 2_000, enabled = true } = options;

  return useQuery<ProcessingJobDTO>({
    queryKey: queryKeys.processing.job(jobId ?? ""),
    queryFn: () => processingService.getJob(jobId as string),
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      const job = query.state.data;
      return job && isActiveJob(job.status) ? refetchIntervalMs : false;
    },
  });
}
