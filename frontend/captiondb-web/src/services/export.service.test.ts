import { describe, expect, it } from "vitest";
import { exportService } from "@/services/export.service";
import type { ProjectResultsData, SceneResultDTO } from "@/types/api";

function makeScene(overrides: Partial<SceneResultDTO> = {}): SceneResultDTO {
  return {
    scene_id: "s1",
    seconds_start: 0,
    seconds_end: 75,
    title: "Opening",
    summary: "A short intro.",
    transcript: null,
    tags: ["intro", "demo"],
    captions: { formal: "Welcome.", humorousTech: "Boot sequence engaged." },
    ...overrides,
  };
}

const data: ProjectResultsData = {
  scenes: [
    makeScene(),
    makeScene({
      scene_id: "s2",
      seconds_start: 75,
      seconds_end: 130,
      title: null,
      summary: null,
      tags: [],
      captions: {},
    }),
  ],
  summary: null,
};

describe("exportService.formats", () => {
  it("exposes txt and json formats with metadata", () => {
    const ids = exportService.formats.map((f) => f.id);
    expect(ids).toContain("txt");
    expect(ids).toContain("json");
    const json = exportService.formats.find((f) => f.id === "json");
    expect(json?.mimeType).toBe("application/json");
    expect(json?.extension).toBe("json");
  });
});

describe("exportService.build (txt)", () => {
  it("appends the extension to the base name", () => {
    const artifact = exportService.build("txt", data, "my-project");
    expect(artifact.filename).toBe("my-project.txt");
    expect(artifact.mimeType).toBe("text/plain");
  });

  it("renders scene header, title, summary, tags, and captions", () => {
    const { content } = exportService.build("txt", data, "p");
    expect(content).toContain("Scene 1 [0:00 - 1:15]");
    expect(content).toContain("Title: Opening");
    expect(content).toContain("Summary: A short intro.");
    expect(content).toContain("Tags: intro, demo");
    expect(content).toContain("Formal: Welcome.");
    expect(content).toContain("Humorous (Tech): Boot sequence engaged.");
  });

  it("omits absent fields for a bare scene", () => {
    const { content } = exportService.build("txt", data, "p");
    // second scene has no title/summary/tags/captions
    expect(content).toContain("Scene 2 [1:15 - 2:10]");
    const secondBlock = content.split("\n\n")[1];
    expect(secondBlock).not.toContain("Title:");
    expect(secondBlock).not.toContain("Captions:");
  });
});

describe("exportService.build (json)", () => {
  it("produces valid, round-trippable JSON of the full data", () => {
    const artifact = exportService.build("json", data, "p");
    expect(artifact.filename).toBe("p.json");
    const parsed = JSON.parse(artifact.content) as ProjectResultsData;
    expect(parsed.scenes).toHaveLength(2);
    expect(parsed.scenes[0]?.title).toBe("Opening");
  });
});

describe("exportService.toCaptionsText", () => {
  it("includes only scenes that have captions", () => {
    const text = exportService.toCaptionsText(data);
    expect(text).toContain("Scene 1 [0:00 - 1:15]");
    expect(text).toContain("Formal: Welcome.");
    // scene 2 has no captions → excluded entirely
    expect(text).not.toContain("Scene 2");
  });

  it("returns an empty string when no scene has captions", () => {
    const empty: ProjectResultsData = {
      scenes: [makeScene({ captions: {} })],
      summary: null,
    };
    expect(exportService.toCaptionsText(empty)).toBe("");
  });
});
