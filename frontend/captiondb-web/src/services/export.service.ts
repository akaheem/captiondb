// ============================================================
// Export Service
// ============================================================
// Pure client-side transforms that turn ProjectResultsData into
// downloadable artifacts. New formats (SRT, VTT, CSV, …) can be added
// by registering another entry in FORMATTERS — components and hooks
// never change.
// ============================================================

import type { ProjectResultsData, SceneResultDTO } from "@/types/api";
import { availableTones, toneLabel } from "@/lib/captions";
import { formatTimecode } from "@/lib/format";

export type ExportFormat = "txt" | "json";

export interface ExportFormatMeta {
  id: ExportFormat;
  label: string;
  extension: string;
  mimeType: string;
}

export interface ExportArtifact {
  content: string;
  filename: string;
  mimeType: string;
}

type Formatter = ExportFormatMeta & {
  build: (data: ProjectResultsData) => string;
};

function sceneToText(scene: SceneResultDTO, index: number): string {
  const lines: string[] = [];
  lines.push(
    `Scene ${index + 1} [${formatTimecode(scene.seconds_start)} - ${formatTimecode(scene.seconds_end)}]`
  );
  if (scene.title) lines.push(`Title: ${scene.title}`);
  if (scene.summary) lines.push(`Summary: ${scene.summary}`);
  if (scene.tags.length) lines.push(`Tags: ${scene.tags.join(", ")}`);

  const tones = availableTones(scene.captions);
  if (tones.length) {
    lines.push("Captions:");
    for (const tone of tones) {
      lines.push(`  - ${toneLabel(tone)}: ${scene.captions[tone]}`);
    }
  }
  return lines.join("\n");
}

const FORMATTERS: Record<ExportFormat, Formatter> = {
  txt: {
    id: "txt",
    label: "Export as TXT",
    extension: "txt",
    mimeType: "text/plain",
    build: (data) =>
      data.scenes.map((scene, i) => sceneToText(scene, i)).join("\n\n"),
  },
  json: {
    id: "json",
    label: "Export as JSON",
    extension: "json",
    mimeType: "application/json",
    build: (data) => JSON.stringify(data, null, 2),
  },
};

export const exportService = {
  /** Formats available for export, in menu order. */
  formats: Object.values(FORMATTERS).map(
    ({ id, label, extension, mimeType }): ExportFormatMeta => ({
      id,
      label,
      extension,
      mimeType,
    })
  ),

  /** Build the export artifact (content + filename + mime) for a format. */
  build(
    format: ExportFormat,
    data: ProjectResultsData,
    baseName: string
  ): ExportArtifact {
    const formatter = FORMATTERS[format];
    return {
      content: formatter.build(data),
      filename: `${baseName}.${formatter.extension}`,
      mimeType: formatter.mimeType,
    };
  },

  /** Plain-text rendering of every caption, suitable for clipboard copy. */
  toCaptionsText(data: ProjectResultsData): string {
    return data.scenes
      .map((scene, i) => {
        const tones = availableTones(scene.captions);
        if (!tones.length) return "";
        const header = `Scene ${i + 1} [${formatTimecode(scene.seconds_start)} - ${formatTimecode(scene.seconds_end)}]`;
        const body = tones
          .map((tone) => `${toneLabel(tone)}: ${scene.captions[tone]}`)
          .join("\n");
        return `${header}\n${body}`;
      })
      .filter(Boolean)
      .join("\n\n");
  },

  /** Trigger a browser download for a built artifact. No-op during SSR. */
  download(artifact: ExportArtifact): void {
    if (typeof window === "undefined") return;
    const blob = new Blob([artifact.content], {
      type: `${artifact.mimeType};charset=utf-8`,
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = artifact.filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  },
} as const;
