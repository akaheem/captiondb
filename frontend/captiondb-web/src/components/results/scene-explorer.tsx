"use client";

import * as React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import type { SceneResultDTO } from "@/types/api";
import { sceneLabel } from "@/lib/scenes";
import { Button } from "@/components/ui/button";
import { SceneCard } from "@/components/results/scene-card";
import { SceneTimeline } from "@/components/results/scene-timeline";
import { SceneMetadata } from "@/components/results/scene-metadata";
import { VisionAnalysisPanel } from "@/components/results/vision-analysis-panel";
import { CaptionViewer } from "@/components/results/caption-viewer";

export interface SceneExplorerProps {
  scenes: SceneResultDTO[];
  initialSceneId?: string;
}

/**
 * Orchestrates scene browsing: a keyboard-navigable sidebar list, a timeline,
 * previous/next controls and the detail panels for the selected scene.
 */
export function SceneExplorer({ scenes, initialSceneId }: SceneExplorerProps) {
  const [selectedId, setSelectedId] = React.useState<string>(
    () => initialSceneId ?? scenes[0]?.scene_id ?? ""
  );

  const selectedIndex = React.useMemo(
    () => Math.max(0, scenes.findIndex((s) => s.scene_id === selectedId)),
    [scenes, selectedId]
  );
  const selectedScene = scenes[selectedIndex] ?? null;

  const selectByIndex = React.useCallback(
    (index: number) => {
      const clamped = Math.min(scenes.length - 1, Math.max(0, index));
      const next = scenes[clamped];
      if (next) setSelectedId(next.scene_id);
    },
    [scenes]
  );

  const handleSelect = React.useCallback(
    (sceneId: string) => setSelectedId(sceneId),
    []
  );

  // Keep the active card visible in the scrollable sidebar.
  React.useEffect(() => {
    const el = document.getElementById(`scene-card-${selectedId}`);
    el?.scrollIntoView({ block: "nearest" });
  }, [selectedId]);

  const handleListKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    switch (event.key) {
      case "ArrowDown":
      case "ArrowRight":
        event.preventDefault();
        selectByIndex(selectedIndex + 1);
        break;
      case "ArrowUp":
      case "ArrowLeft":
        event.preventDefault();
        selectByIndex(selectedIndex - 1);
        break;
      case "Home":
        event.preventDefault();
        selectByIndex(0);
        break;
      case "End":
        event.preventDefault();
        selectByIndex(scenes.length - 1);
        break;
    }
  };

  if (!selectedScene) return null;

  return (
    <div className="space-y-4">
      <SceneTimeline
        scenes={scenes}
        activeSceneId={selectedId}
        onSelect={handleSelect}
        positionSeconds={selectedScene.seconds_start}
      />

      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        {/* Sidebar navigation */}
        <div
          role="listbox"
          aria-label="Scenes"
          aria-activedescendant={`scene-card-${selectedId}`}
          tabIndex={0}
          onKeyDown={handleListKeyDown}
          className="max-h-[70vh] space-y-2 overflow-y-auto rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-ring lg:pr-1"
        >
          {scenes.map((scene, index) => (
            <SceneCard
              key={scene.scene_id}
              scene={scene}
              index={index}
              isActive={scene.scene_id === selectedId}
              onSelect={handleSelect}
            />
          ))}
        </div>

        {/* Detail panel */}
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-2">
            <h2 className="truncate text-lg font-semibold">
              {sceneLabel(selectedScene, selectedIndex)}
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground tabular-nums">
                Scene {selectedIndex + 1} of {scenes.length}
              </span>
              <Button
                variant="outline"
                size="icon-sm"
                aria-label="Previous scene"
                disabled={selectedIndex === 0}
                onClick={() => selectByIndex(selectedIndex - 1)}
              >
                <ChevronLeft aria-hidden="true" />
              </Button>
              <Button
                variant="outline"
                size="icon-sm"
                aria-label="Next scene"
                disabled={selectedIndex === scenes.length - 1}
                onClick={() => selectByIndex(selectedIndex + 1)}
              >
                <ChevronRight aria-hidden="true" />
              </Button>
            </div>
          </div>

          <SceneMetadata scene={selectedScene} />
          <VisionAnalysisPanel scene={selectedScene} />
          <CaptionViewer scene={selectedScene} />
        </div>
      </div>
    </div>
  );
}
