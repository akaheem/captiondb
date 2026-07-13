"use client";

import type { SceneResultDTO } from "@/types/api";
import { formatDuration, formatTimecode } from "@/lib/format";
import { sceneDuration } from "@/lib/scenes";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Field, NotAvailable, TagList } from "@/components/results/shared";

export interface SceneMetadataProps {
  scene: SceneResultDTO;
}

/** Structural metadata for a scene: timestamps, duration, id, thumbnail, tags. */
export function SceneMetadata({ scene }: SceneMetadataProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Scene Metadata</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3">
          <Field label="Scene ID">
            <span className="font-mono text-xs break-all">{scene.scene_id}</span>
          </Field>
          <Field label="Start">{formatTimecode(scene.seconds_start)}</Field>
          <Field label="End">{formatTimecode(scene.seconds_end)}</Field>
          <Field label="Duration">{formatDuration(sceneDuration(scene))}</Field>
          <Field label="Thumbnail">
            {scene.thumbnail_url ? "Available" : <NotAvailable />}
          </Field>
          <Field label="Tags">
            <TagList items={scene.tags} />
          </Field>
        </dl>
      </CardContent>
    </Card>
  );
}
