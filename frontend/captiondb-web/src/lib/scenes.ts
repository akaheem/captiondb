// ============================================================
// Scene helpers
// ============================================================
// Derivations over merged scene results, kept out of components.
// ============================================================

import type { SceneResultDTO } from "@/types/api";
import { availableTones } from "@/lib/captions";

export type SceneStatus = "processed" | "pending";

/** A scene counts as processed once it has a summary or at least one caption. */
export function getSceneStatus(scene: SceneResultDTO): SceneStatus {
  const hasCaptions = availableTones(scene.captions).length > 0;
  return scene.summary || hasCaptions ? "processed" : "pending";
}

export function sceneDuration(scene: SceneResultDTO): number {
  return Math.max(0, scene.seconds_end - scene.seconds_start);
}

/** Best available display label for a scene. */
export function sceneLabel(scene: SceneResultDTO, index: number): string {
  return scene.title?.trim() || `Scene ${index + 1}`;
}
