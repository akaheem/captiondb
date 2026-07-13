"use client";

import type { SceneResultDTO } from "@/types/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Field, NotAvailable, TagList } from "@/components/results/shared";

export interface VisionAnalysisPanelProps {
  scene: SceneResultDTO;
}

/** Color swatches for dominant colors, or "Not available". */
function ColorSwatches({ colors }: { colors?: string[] }) {
  if (!colors || colors.length === 0) return <NotAvailable />;
  return (
    <ul className="flex flex-wrap gap-2">
      {colors.map((color, i) => (
        <li key={`${color}-${i}`} className="flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className="h-4 w-4 rounded-full border border-border"
            style={{ backgroundColor: color }}
          />
          <span className="text-xs text-muted-foreground">{color}</span>
        </li>
      ))}
    </ul>
  );
}

/**
 * AI vision analysis for a scene. Only `summary` is exposed by the API today;
 * every other field degrades to "Not available" and lights up automatically if
 * the backend starts returning it. Missing fields never crash the panel.
 */
export function VisionAnalysisPanel({ scene }: VisionAnalysisPanelProps) {
  const confidence =
    typeof scene.confidence === "number"
      ? `${Math.round(scene.confidence * 100)}%`
      : undefined;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Vision Analysis</CardTitle>
        <CardDescription>AI-extracted understanding of the scene.</CardDescription>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Field label="Summary" value={scene.summary} />
          </div>
          <Field label="Objects">
            <TagList items={scene.objects} />
          </Field>
          <Field label="Activities">
            <TagList items={scene.activities} />
          </Field>
          <Field label="Dominant Colors">
            <ColorSwatches colors={scene.dominant_colors} />
          </Field>
          <Field label="Safety Flags">
            <TagList items={scene.safety_flags} />
          </Field>
          <div className="sm:col-span-2">
            <Field label="OCR Text" value={scene.ocr_text} />
          </div>
          <Field label="AI Confidence" value={confidence} />
        </dl>
      </CardContent>
    </Card>
  );
}
