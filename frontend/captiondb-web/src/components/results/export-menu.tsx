"use client";

import { ChevronDown, ClipboardCopy, Download } from "lucide-react";

import { useExportResults } from "@/hooks/use-results";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export interface ExportMenuProps {
  projectId: string;
}

/**
 * Export actions for a project's results: copy captions to the clipboard, or
 * download in any registered format (TXT, JSON — SRT/VTT/CSV can be added in
 * the export service with no change here).
 */
export function ExportMenu({ projectId }: ExportMenuProps) {
  const { exportAs, copyCaptions, formats, isReady } = useExportResults(projectId);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger disabled={!isReady}>
        <Button variant="outline" disabled={!isReady}>
          <Download aria-hidden="true" />
          Export
          <ChevronDown aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => copyCaptions()}>
          <ClipboardCopy aria-hidden="true" />
          Copy captions
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {formats.map((format) => (
          <DropdownMenuItem key={format.id} onClick={() => exportAs(format.id)}>
            <Download aria-hidden="true" />
            {format.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
