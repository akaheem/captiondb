// ============================================================
// Results API Service
// ============================================================
// The ONLY place that calls the AI-results endpoints. Fetches the
// scene list, caption sets and summary for a project and merges them
// into the ProjectResultsData shape the Scene Explorer renders.
// Components must never call apiClient directly.
// ============================================================

import { apiClient } from "@/lib/api-client";
import type {
  CaptionListResponse,
  ProjectResultsData,
  ProjectSummaryDTO,
  SceneListResponse,
  SceneResultDTO,
} from "@/types/api";

const PROJECT_BASE = "/v1/projects";

export const resultsService = {
  /** Raw scenes for a project. */
  async getScenes(projectId: string): Promise<SceneListResponse> {
    return apiClient.get<SceneListResponse>(
      `${PROJECT_BASE}/${projectId}/scenes`
    );
  },

  /** Per-scene caption sets (keyed by tone). */
  async getCaptions(projectId: string): Promise<CaptionListResponse> {
    return apiClient.get<CaptionListResponse>(
      `${PROJECT_BASE}/${projectId}/captions`
    );
  },

  /** Aggregate project statistics. */
  async getSummary(projectId: string): Promise<ProjectSummaryDTO> {
    return apiClient.get<ProjectSummaryDTO>(
      `${PROJECT_BASE}/${projectId}/summary`
    );
  },

  /**
   * Fetch scenes, captions and summary together and merge them into the
   * render-ready ProjectResultsData. Captions are joined onto their scene by
   * scene_id; the summary is best-effort (null if unavailable).
   */
  async getProjectResults(projectId: string): Promise<ProjectResultsData> {
    const [scenesRes, captionsRes, summary] = await Promise.all([
      this.getScenes(projectId),
      this.getCaptions(projectId).catch(() => ({ data: [], total: 0 })),
      this.getSummary(projectId).catch(() => null),
    ]);

    const captionsByScene = new Map(
      captionsRes.data.map((c) => [c.scene_id, c.captions])
    );

    const scenes: SceneResultDTO[] = scenesRes.data.map((scene) => ({
      scene_id: scene.scene_id,
      seconds_start: scene.seconds_start,
      seconds_end: scene.seconds_end,
      title: scene.title ?? null,
      summary: scene.summary ?? null,
      transcript: scene.transcript ?? null,
      tags: scene.tags ?? [],
      captions: captionsByScene.get(scene.scene_id) ?? {},
    }));

    return { scenes, summary };
  },
} as const;
