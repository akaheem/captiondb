"use client";

import { ProcessingMonitor } from "@/components/dashboard/processing-monitor";

export default function ProcessingPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Processing</h1>
        <p className="text-muted-foreground">
          Monitor AI processing jobs in real time.
        </p>
      </div>

      <ProcessingMonitor
        title="All Jobs"
        description="Every AI processing job, updated live while work is in progress."
      />
    </div>
  );
}
