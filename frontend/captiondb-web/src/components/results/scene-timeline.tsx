"use client";

import * as React from "react";

import type { SceneResultDTO } from "@/types/api";
import { cn } from "@/lib/utils";
import { formatTimecode } from "@/lib/format";
import { getSceneStatus, sceneLabel } from "@/lib/scenes";

export interface SceneTimelineProps {
  scenes: SceneResultDTO[];
  activeSceneId: string | null;
  onSelect: (sceneId: string) => void;
  /** Optional playback head position, in seconds. */
  positionSeconds?: number;
}

function SceneTimelineImpl({
  scenes,
  activeSceneId,
  onSelect,
  positionSeconds,
}: SceneTimelineProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null);

  const totalSeconds = React.useMemo(
    () => scenes.reduce((max, s) => Math.max(max, s.seconds_end), 0),
    [scenes]
  );

  // Auto-scroll the active segment into view when the selection changes.
  React.useEffect(() => {
    if (!activeSceneId || !scrollRef.current) return;
    const el = scrollRef.current.querySelector<HTMLElement>(
      `[data-scene-id="${activeSceneId}"]`
    );
    el?.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
  }, [activeSceneId]);

  if (scenes.length === 0 || totalSeconds <= 0) return null;

  const headLeft =
    positionSeconds != null
      ? `${Math.min(100, Math.max(0, (positionSeconds / totalSeconds) * 100))}%`
      : null;

  return (
    <div
      ref={scrollRef}
      role="group"
      aria-label="Scene timeline"
      className="relative overflow-x-auto rounded-lg border bg-card p-2"
    >
      <div className="relative flex h-10 min-w-full gap-0.5">
        {scenes.map((scene, index) => {
          const isActive = scene.scene_id === activeSceneId;
          const widthPct = Math.max(
            2,
            ((scene.seconds_end - scene.seconds_start) / totalSeconds) * 100
          );
          const status = getSceneStatus(scene);
          return (
            <button
              key={scene.scene_id}
              type="button"
              data-scene-id={scene.scene_id}
              onClick={() => onSelect(scene.scene_id)}
              aria-current={isActive ? "true" : undefined}
              aria-label={`${sceneLabel(scene, index)}, ${formatTimecode(
                scene.seconds_start
              )} to ${formatTimecode(scene.seconds_end)}`}
              style={{ width: `${widthPct}%` }}
              className={cn(
                "group relative flex h-full min-w-[2rem] items-center justify-center overflow-hidden rounded-md border text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                isActive
                  ? "border-primary bg-primary/15 text-foreground"
                  : status === "processed"
                    ? "border-border bg-muted hover:bg-muted/70 text-muted-foreground"
                    : "border-dashed border-border bg-background text-muted-foreground hover:bg-muted/50"
              )}
            >
              <span className="truncate px-1 tabular-nums">{index + 1}</span>
            </button>
          );
        })}

        {headLeft && (
          <div
            aria-hidden="true"
            className="pointer-events-none absolute top-0 bottom-0 z-10 w-0.5 bg-primary"
            style={{ left: headLeft }}
          />
        )}
      </div>
    </div>
  );
}

/** Memoized — only re-renders when scenes, selection or playhead change. */
export const SceneTimeline = React.memo(SceneTimelineImpl);
