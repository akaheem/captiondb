// ============================================================
// Processing / AI Jobs API Service
// ============================================================
// The ONLY place that calls the AI processing-job endpoints.
// Pages/components call hooks (use-processing) that call this service.
// ============================================================

import { apiClient } from "@/lib/api-client";
import type {
  ProcessingJobDTO,
  ProcessingJobListResponse,
} from "@/types/api";

const PROCESSING_BASE = "/v1/processing";

export const processingService = {
  /** List AI processing jobs (optionally filtered by status). */
  async listJobs(
    params: { status?: string; limit?: number; offset?: number } = {}
  ): Promise<ProcessingJobListResponse> {
    return apiClient.get<ProcessingJobListResponse>(`${PROCESSING_BASE}/jobs`, {
      params,
    });
  },

  /** Get a single job's live status, progress and logs. */
  async getJob(jobId: string): Promise<ProcessingJobDTO> {
    return apiClient.get<ProcessingJobDTO>(`${PROCESSING_BASE}/jobs/${jobId}`);
  },
} as const;
