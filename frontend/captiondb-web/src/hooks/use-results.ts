// ============================================================
// AI Results — React Query hooks
// ============================================================
// Reads merged scene/caption/summary data through resultsService and
// exposes client-side export helpers via exportService. All caching
// flows through the shared query-key factory.
// ============================================================

import { useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { resultsService } from "@/services/results.service";
import { exportService, type ExportFormat } from "@/services/export.service";
import { queryKeys } from "@/lib/query-keys";
import type { ProjectResultsData, SceneResultDTO } from "@/types/api";

/** Merged scenes + captions + summary for a project. */
export function useProjectResults(projectId: string | null | undefined) {
  return useQuery<ProjectResultsData>({
    queryKey: queryKeys.results.byProject(projectId ?? ""),
    queryFn: () => resultsService.getProjectResults(projectId as string),
    enabled: !!projectId,
  });
}

/**
 * A single merged scene, selected from the project results cache (the backend
 * has no per-scene endpoint, so this shares the project-results query).
 */
export function useScene(
  projectId: string | null | undefined,
  sceneId: string | null | undefined
) {
  return useQuery<ProjectResultsData, Error, SceneResultDTO | null>({
    queryKey: queryKeys.results.byProject(projectId ?? ""),
    queryFn: () => resultsService.getProjectResults(projectId as string),
    enabled: !!projectId && !!sceneId,
    select: (data) =>
      data.scenes.find((scene) => scene.scene_id === sceneId) ?? null,
  });
}

/**
 * Client-side export helpers for a project's results. Reads the already-cached
 * results (falling back to a fetch) and produces downloads / clipboard copies.
 */
export function useExportResults(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  const { data, isLoading } = useProjectResults(projectId);

  const resolveData = useCallback(async (): Promise<ProjectResultsData | null> => {
    if (data) return data;
    if (!projectId) return null;
    return queryClient.fetchQuery({
      queryKey: queryKeys.results.byProject(projectId),
      queryFn: () => resultsService.getProjectResults(projectId),
    });
  }, [data, projectId, queryClient]);

  const exportAs = useCallback(
    async (format: ExportFormat) => {
      const results = await resolveData();
      if (!results || results.scenes.length === 0) {
        toast.error("Nothing to export yet");
        return;
      }
      const artifact = exportService.build(
        format,
        results,
        `captiondb-${projectId ?? "results"}`
      );
      exportService.download(artifact);
      toast.success(`Exported ${format.toUpperCase()}`);
    },
    [resolveData, projectId]
  );

  const copyCaptions = useCallback(async () => {
    const results = await resolveData();
    const text = results ? exportService.toCaptionsText(results) : "";
    if (!text) {
      toast.error("No captions to copy");
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Captions copied to clipboard");
    } catch {
      toast.error("Unable to copy captions");
    }
  }, [resolveData]);

  return {
    exportAs,
    copyCaptions,
    formats: exportService.formats,
    isReady: !!data && data.scenes.length > 0,
    isLoading,
  };
}
