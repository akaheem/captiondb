"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { useProject } from "@/hooks/use-projects";
import { useProjectResults } from "@/hooks/use-results";
import { Button } from "@/components/ui/button";
import { ResultStatistics } from "@/components/results/result-statistics";
import { SceneExplorer } from "@/components/results/scene-explorer";
import { ExportMenu } from "@/components/results/export-menu";
import { ResultsSkeleton } from "@/components/results/results-skeleton";

export default function ProjectResultsPage() {
  const params = useParams();
  const projectId = params.id as string;

  const { data: project } = useProject(projectId);
  const {
    data: results,
    isLoading,
    isError,
    refetch,
  } = useProjectResults(projectId);

  const scenes = results?.scenes ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href={`/dashboard/projects/${projectId}`} aria-label="Back to project">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {project?.project_name ?? "Results"}
            </h1>
            <p className="text-muted-foreground">AI results &amp; scene explorer</p>
          </div>
        </div>
        <ExportMenu projectId={projectId} />
      </div>

      {isLoading ? (
        <ResultsSkeleton />
      ) : isError ? (
        <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-destructive/20 bg-destructive/10 p-8 text-center text-destructive">
          <h3 className="text-lg font-semibold">Unable to load results</h3>
          <p className="text-sm">Something went wrong while fetching AI results.</p>
          <Button variant="outline" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      ) : scenes.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
          <h3 className="text-lg font-semibold">No results yet</h3>
          <p className="mt-1 mb-4 text-sm text-muted-foreground">
            This project has no analyzed scenes. Run AI processing to generate results.
          </p>
          <Link href={`/dashboard/projects/${projectId}`}>
            <Button variant="outline">Back to Project</Button>
          </Link>
        </div>
      ) : (
        <>
          <ResultStatistics summary={results?.summary ?? null} sceneCount={scenes.length} />
          <SceneExplorer scenes={scenes} />
        </>
      )}
    </div>
  );
}
