// ============================================================
// Caption tone helpers
// ============================================================
// Shared, presentation-agnostic metadata for caption tones so the
// viewer and exporters stay in sync.
// ============================================================

import type { CaptionSet, CaptionTone } from "@/types/api";

/** Human-readable labels for each backend caption tone. */
export const CAPTION_TONE_LABELS: Record<CaptionTone, string> = {
  formal: "Formal",
  sarcastic: "Sarcastic",
  humorousTech: "Humorous (Tech)",
  humorousNonTech: "Humorous (Non-Tech)",
  audio: "Audio Description",
  none: "Plain",
};

/** Stable display order for tones. */
export const CAPTION_TONE_ORDER: CaptionTone[] = [
  "formal",
  "humorousTech",
  "humorousNonTech",
  "sarcastic",
  "audio",
  "none",
];

export function toneLabel(tone: CaptionTone): string {
  return CAPTION_TONE_LABELS[tone] ?? tone;
}

/**
 * Return the tones present in a caption set (non-empty text), in display order.
 */
export function availableTones(captions: CaptionSet | undefined): CaptionTone[] {
  if (!captions) return [];
  return CAPTION_TONE_ORDER.filter((tone) => {
    const text = captions[tone];
    return typeof text === "string" && text.trim().length > 0;
  });
}
