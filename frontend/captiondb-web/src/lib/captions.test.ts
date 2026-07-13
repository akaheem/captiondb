import { describe, expect, it } from "vitest";
import {
  CAPTION_TONE_ORDER,
  availableTones,
  toneLabel,
} from "@/lib/captions";
import type { CaptionSet } from "@/types/api";

describe("toneLabel", () => {
  it("maps known tones to human labels", () => {
    expect(toneLabel("formal")).toBe("Formal");
    expect(toneLabel("humorousTech")).toBe("Humorous (Tech)");
    expect(toneLabel("none")).toBe("Plain");
  });

  it("falls back to the raw tone when unmapped", () => {
    // @ts-expect-error — exercising the runtime fallback branch
    expect(toneLabel("mystery")).toBe("mystery");
  });
});

describe("availableTones", () => {
  it("returns tones with non-empty text in display order", () => {
    const captions: CaptionSet = {
      none: "plain text",
      formal: "formal text",
      humorousTech: "techie",
    };
    // display order is formal → humorousTech → … → none
    expect(availableTones(captions)).toEqual([
      "formal",
      "humorousTech",
      "none",
    ]);
  });

  it("skips empty and whitespace-only captions", () => {
    const captions: CaptionSet = {
      formal: "",
      sarcastic: "   ",
      audio: "described",
    };
    expect(availableTones(captions)).toEqual(["audio"]);
  });

  it("returns an empty array for undefined or empty input", () => {
    expect(availableTones(undefined)).toEqual([]);
    expect(availableTones({})).toEqual([]);
  });

  it("never returns a tone outside the canonical order", () => {
    const captions: CaptionSet = { formal: "x", none: "y" };
    for (const tone of availableTones(captions)) {
      expect(CAPTION_TONE_ORDER).toContain(tone);
    }
  });
});
