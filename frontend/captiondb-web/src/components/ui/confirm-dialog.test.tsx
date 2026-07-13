import type * as React from "react";
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";

function setup(overrides: Partial<React.ComponentProps<typeof ConfirmDialog>> = {}) {
  const onConfirm = vi.fn();
  const onOpenChange = vi.fn();
  render(
    <ConfirmDialog
      open
      onOpenChange={onOpenChange}
      title="Delete project"
      description="This cannot be undone."
      confirmLabel="Delete"
      onConfirm={onConfirm}
      {...overrides}
    />
  );
  return { onConfirm, onOpenChange };
}

describe("ConfirmDialog", () => {
  it("renders title, description, and action labels when open", () => {
    setup();
    expect(screen.getByText("Delete project")).toBeInTheDocument();
    expect(screen.getByText("This cannot be undone.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("renders nothing when closed", () => {
    setup({ open: false });
    expect(screen.queryByText("Delete project")).not.toBeInTheDocument();
  });

  it("invokes onConfirm when the confirm button is clicked", async () => {
    const user = userEvent.setup();
    const { onConfirm } = setup();
    await user.click(screen.getByRole("button", { name: "Delete" }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("requests close via onOpenChange when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const { onOpenChange, onConfirm } = setup();
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    // base-ui passes (open, eventDetails) — assert on the open arg only.
    expect(onOpenChange).toHaveBeenCalled();
    expect(onOpenChange.mock.calls[0]?.[0]).toBe(false);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("disables both actions while loading", () => {
    setup({ loading: true });
    expect(screen.getByRole("button", { name: "Delete" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });

  it("omits the description node when none is provided", () => {
    setup({ description: undefined });
    expect(screen.queryByText("This cannot be undone.")).not.toBeInTheDocument();
  });
});
