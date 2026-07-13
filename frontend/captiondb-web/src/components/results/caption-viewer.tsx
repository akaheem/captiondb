"use client";

import * as React from "react";
import { Check, Copy, Download } from "lucide-react";
import { toast } from "sonner";

import type { CaptionTone, SceneResultDTO } from "@/types/api";
import { availableTones, toneLabel } from "@/lib/captions";
import { exportService } from "@/services/export.service";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsList, TabsPanel, TabsTab } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export interface CaptionViewerProps {
  scene: SceneResultDTO;
}

function CaptionPanel({
  scene,
  tone,
}: {
  scene: SceneResultDTO;
  tone: CaptionTone;
}) {
  const text = scene.captions[tone] ?? "";
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success("Caption copied");
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("Unable to copy caption");
    }
  };

  const handleDownload = () => {
    exportService.download({
      content: text,
      filename: `caption-${scene.scene_id}-${tone}.txt`,
      mimeType: "text/plain",
    });
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Badge variant="secondary">{toneLabel(tone)}</Badge>
        <span
          className="text-xs text-muted-foreground tabular-nums"
          aria-label={`${text.length} characters`}
        >
          {text.length} chars
        </span>
      </div>
      <p className="rounded-lg border bg-muted/30 p-3 text-sm whitespace-pre-wrap">
        {text}
      </p>
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" size="sm" onClick={handleCopy}>
          {copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
          {copied ? "Copied" : "Copy"}
        </Button>
        <Button variant="outline" size="sm" onClick={handleDownload}>
          <Download aria-hidden="true" />
          Download
        </Button>
      </div>
    </div>
  );
}

/**
 * Shows generated captions for a scene. When multiple caption candidates
 * (tones) exist, they are switchable via Tabs. Degrades to an empty state
 * when nothing has been generated.
 */
export function CaptionViewer({ scene }: CaptionViewerProps) {
  const tones = availableTones(scene.captions);
  const [firstTone] = tones;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Captions</CardTitle>
        <CardDescription>
          AI-generated captions{tones.length > 1 ? " across tones" : ""}.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {tones.length === 0 ? (
          <p className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
            No captions generated for this scene yet.
          </p>
        ) : tones.length === 1 && firstTone ? (
          <CaptionPanel scene={scene} tone={firstTone} />
        ) : (
          <Tabs defaultValue={firstTone}>
            <TabsList aria-label="Caption tones">
              {tones.map((tone) => (
                <TabsTab key={tone} value={tone}>
                  {toneLabel(tone)}
                </TabsTab>
              ))}
            </TabsList>
            {tones.map((tone) => (
              <TabsPanel key={tone} value={tone} className="pt-2">
                <CaptionPanel scene={scene} tone={tone} />
              </TabsPanel>
            ))}
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}
