"use client";

import * as React from "react";
import { Film } from "lucide-react";

import type { SceneResultDTO } from "@/types/api";
import { cn } from "@/lib/utils";
import { formatDuration, formatTimecode } from "@/lib/format";
import { getSceneStatus, sceneDuration, sceneLabel } from "@/lib/scenes";
import { Badge } from "@/components/ui/badge";

export interface SceneCardProps {
  scene: SceneResultDTO;
  index: number;
  isActive: boolean;
  onSelect: (sceneId: string) => void;
}

/** Thumbnail tile — real image when available, placeholder otherwise. */
function Thumbnail({ scene }: { scene: SceneResultDTO }) {
  if (scene.thumbnail_url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={scene.thumbnail_url}
        alt=""
        className="h-12 w-16 shrink-0 rounded-md object-cover"
      />
    );
  }
  return (
    <div
      aria-hidden="true"
      className="flex h-12 w-16 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground"
    >
      <Film className="h-5 w-5" />
    </div>
  );
}

function SceneCardImpl({ scene, index, isActive, onSelect }: SceneCardProps) {
  const status = getSceneStatus(scene);
  const label = sceneLabel(scene, index);

  return (
    <div
      id={`scene-card-${scene.scene_id}`}
      role="option"
      aria-selected={isActive}
      onClick={() => onSelect(scene.scene_id)}
      className={cn(
        "flex cursor-pointer items-center gap-3 rounded-lg border p-2 text-left transition-colors",
        isActive
          ? "border-primary bg-primary/5 ring-1 ring-primary"
          : "border-border hover:bg-muted/50"
      )}
    >
      <Thumbnail scene={scene} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-muted-foreground tabular-nums">
            #{index + 1}
          </span>
          <span className="truncate text-sm font-medium">{label}</span>
        </div>
        <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground tabular-nums">
          <span>
            {formatTimecode(scene.seconds_start)} – {formatTimecode(scene.seconds_end)}
          </span>
          <span aria-hidden="true">·</span>
          <span>{formatDuration(sceneDuration(scene))}</span>
        </div>
      </div>
      <Badge variant={status === "processed" ? "success" : "muted"}>
        {status === "processed" ? "Processed" : "Pending"}
      </Badge>
    </div>
  );
}

/** Memoized so unaffected cards don't re-render when the selection changes. */
export const SceneCard = React.memo(SceneCardImpl);
