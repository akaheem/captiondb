import { describe, expect, it } from "vitest";
import { getSceneStatus, sceneDuration, sceneLabel } from "@/lib/scenes";
import type { SceneResultDTO } from "@/types/api";

function makeScene(overrides: Partial<SceneResultDTO> = {}): SceneResultDTO {
  return {
    scene_id: "s1",
    seconds_start: 0,
    seconds_end: 10,
    title: null,
    summary: null,
    transcript: null,
    tags: [],
    captions: {},
    ...overrides,
  };
}

describe("getSceneStatus", () => {
  it("is 'processed' when a summary exists", () => {
    expect(getSceneStatus(makeScene({ summary: "a summary" }))).toBe(
      "processed"
    );
  });

  it("is 'processed' when at least one caption exists", () => {
    expect(
      getSceneStatus(makeScene({ captions: { formal: "hi" } }))
    ).toBe("processed");
  });

  it("is 'pending' with no summary and no captions", () => {
    expect(getSceneStatus(makeScene())).toBe("pending");
    expect(
      getSceneStatus(makeScene({ captions: { formal: "  " } }))
    ).toBe("pending");
  });
});

describe("sceneDuration", () => {
  it("returns end minus start", () => {
    expect(sceneDuration(makeScene({ seconds_start: 5, seconds_end: 12 }))).toBe(
      7
    );
  });

  it("clamps inverted ranges to zero", () => {
    expect(
      sceneDuration(makeScene({ seconds_start: 20, seconds_end: 10 }))
    ).toBe(0);
  });
});

describe("sceneLabel", () => {
  it("prefers a trimmed title", () => {
    expect(sceneLabel(makeScene({ title: "  Intro  " }), 0)).toBe("Intro");
  });

  it("falls back to a 1-based index when title is empty/whitespace/null", () => {
    expect(sceneLabel(makeScene({ title: null }), 0)).toBe("Scene 1");
    expect(sceneLabel(makeScene({ title: "   " }), 4)).toBe("Scene 5");
  });
});
