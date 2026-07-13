import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  formatBytes,
  formatDateTime,
  formatDuration,
  formatRelativeTime,
  formatTimecode,
} from "@/lib/format";

describe("formatTimecode", () => {
  it("formats sub-hour durations as m:ss", () => {
    expect(formatTimecode(0)).toBe("0:00");
    expect(formatTimecode(5)).toBe("0:05");
    expect(formatTimecode(75)).toBe("1:15");
    expect(formatTimecode(600)).toBe("10:00");
  });

  it("formats hour-plus durations as h:mm:ss with padding", () => {
    expect(formatTimecode(3600)).toBe("1:00:00");
    expect(formatTimecode(3675)).toBe("1:01:15");
  });

  it("floors fractional seconds and clamps negatives to zero", () => {
    expect(formatTimecode(75.9)).toBe("1:15");
    expect(formatTimecode(-10)).toBe("0:00");
  });

  it("returns 0:00 for null, undefined, and non-finite input", () => {
    expect(formatTimecode(null)).toBe("0:00");
    expect(formatTimecode(undefined)).toBe("0:00");
    expect(formatTimecode(NaN)).toBe("0:00");
    expect(formatTimecode(Infinity)).toBe("0:00");
  });
});

describe("formatDuration", () => {
  it("shows one decimal for sub-minute durations", () => {
    expect(formatDuration(5)).toBe("5.0s");
    expect(formatDuration(0)).toBe("0.0s");
    expect(formatDuration(59.4)).toBe("59.4s");
  });

  it("shows minutes and seconds, dropping zero seconds", () => {
    expect(formatDuration(90)).toBe("1m 30s");
    expect(formatDuration(120)).toBe("2m");
  });

  it("shows hours and minutes, dropping zero minutes", () => {
    expect(formatDuration(3600)).toBe("1h");
    expect(formatDuration(3900)).toBe("1h 5m");
  });

  it("returns an em dash for null/undefined/non-finite", () => {
    expect(formatDuration(null)).toBe("—");
    expect(formatDuration(undefined)).toBe("—");
    expect(formatDuration(NaN)).toBe("—");
  });
});

describe("formatBytes", () => {
  it("formats across unit boundaries", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(1024)).toBe("1 KB");
    expect(formatBytes(1536)).toBe("1.5 KB");
    expect(formatBytes(1024 * 1024)).toBe("1 MB");
    expect(formatBytes(1024 * 1024 * 1024)).toBe("1 GB");
  });

  it("returns 0 B for zero, negative, null, and non-finite", () => {
    expect(formatBytes(0)).toBe("0 B");
    expect(formatBytes(-5)).toBe("0 B");
    expect(formatBytes(null)).toBe("0 B");
    expect(formatBytes(undefined)).toBe("0 B");
    expect(formatBytes(NaN)).toBe("0 B");
  });
});

describe("formatDateTime", () => {
  it("returns an em dash for empty/invalid input", () => {
    expect(formatDateTime(null)).toBe("—");
    expect(formatDateTime(undefined)).toBe("—");
    expect(formatDateTime("")).toBe("—");
    expect(formatDateTime("not-a-date")).toBe("—");
  });

  it("renders a valid ISO string to a non-empty localized label", () => {
    const out = formatDateTime("2026-07-13T15:26:00Z");
    expect(out).not.toBe("—");
    expect(out).toContain("2026");
  });
});

describe("formatRelativeTime", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-13T12:00:00Z"));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  const ago = (ms: number) => new Date(Date.now() - ms).toISOString();

  it("returns 'just now' under 45 seconds", () => {
    expect(formatRelativeTime(ago(10_000))).toBe("just now");
  });

  it("returns minutes, hours, days, months, years", () => {
    expect(formatRelativeTime(ago(5 * 60_000))).toBe("5m ago");
    expect(formatRelativeTime(ago(3 * 3600_000))).toBe("3h ago");
    expect(formatRelativeTime(ago(2 * 86_400_000))).toBe("2d ago");
    expect(formatRelativeTime(ago(60 * 86_400_000))).toBe("2mo ago");
    expect(formatRelativeTime(ago(400 * 86_400_000))).toBe("1y ago");
  });

  it("returns an em dash for empty/invalid input", () => {
    expect(formatRelativeTime(null)).toBe("—");
    expect(formatRelativeTime("nope")).toBe("—");
  });
});
