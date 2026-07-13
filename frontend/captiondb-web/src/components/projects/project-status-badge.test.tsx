import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProjectStatusBadge } from "@/components/projects/project-status-badge";
import type { VideoStatus } from "@/types/api";

describe("ProjectStatusBadge", () => {
  it.each([
    ["PENDING", "Pending"],
    ["PROCESSING", "Processing"],
    ["COMPLETED", "Completed"],
    ["FAILED", "Failed"],
  ] as const)("renders the %s label", (status, label) => {
    render(<ProjectStatusBadge status={status} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });

  it("falls back to the raw status for an unknown value", () => {
    render(<ProjectStatusBadge status={"ARCHIVED" as VideoStatus} />);
    expect(screen.getByText("ARCHIVED")).toBeInTheDocument();
  });
});
