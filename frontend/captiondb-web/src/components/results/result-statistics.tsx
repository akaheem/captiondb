"use client";

import type { ProjectSummaryDTO } from "@/types/api";
import { formatDuration } from "@/lib/format";
import { Card, CardContent } from "@/components/ui/card";
import { NotAvailable } from "@/components/results/shared";

export interface ResultStatisticsProps {
  summary: ProjectSummaryDTO | null;
  /** Fallback scene count when the summary endpoint is unavailable. */
  sceneCount: number;
}

interface Stat {
  label: string;
  value: React.ReactNode;
}

function StatTile({ label, value }: Stat) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          {label}
        </p>
        <div className="mt-1 text-2xl font-bold tabular-nums">{value}</div>
      </CardContent>
    </Card>
  );
}

/** Aggregate statistics for a project's AI results. */
export function ResultStatistics({ summary, sceneCount }: ResultStatisticsProps) {
  const total = summary?.total_scenes ?? sceneCount;
  const processed = summary?.successful_scenes ?? null;
  const failed =
    summary != null ? Math.max(0, summary.total_scenes - summary.successful_scenes) : null;

  const stats: Stat[] = [
    { label: "Total Scenes", value: total },
    { label: "Processed", value: processed ?? <NotAvailable /> },
    { label: "Failed", value: failed ?? <NotAvailable /> },
    {
      label: "Captions",
      value: summary?.total_captions ?? <NotAvailable />,
    },
    {
      label: "Duration",
      value: summary ? formatDuration(summary.processing_duration_seconds) : <NotAvailable />,
    },
    {
      label: "Token Usage",
      value: summary?.token_usage ?? <NotAvailable />,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      {stats.map((stat) => (
        <StatTile key={stat.label} {...stat} />
      ))}
    </div>
  );
}
