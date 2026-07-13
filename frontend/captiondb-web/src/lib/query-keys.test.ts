import { describe, expect, it } from "vitest";
import { queryKeys } from "@/lib/query-keys";

describe("queryKeys", () => {
  it("nests session keys under auth → sessions", () => {
    expect(queryKeys.auth.all).toEqual(["auth"]);
    expect(queryKeys.auth.sessions()).toEqual(["auth", "sessions"]);
    expect(queryKeys.auth.session("abc")).toEqual(["auth", "sessions", "abc"]);
  });

  it("nests user keys", () => {
    expect(queryKeys.user.me()).toEqual(["user", "me"]);
    expect(queryKeys.user.byId("u1")).toEqual(["user", "u1"]);
  });

  it("includes filters in the projects list key so invalidation is scoped", () => {
    expect(queryKeys.projects.list()).toEqual(["projects", "list", undefined]);
    const filters = { status: "COMPLETED", offset: 10 };
    expect(queryKeys.projects.list(filters)).toEqual([
      "projects",
      "list",
      filters,
    ]);
    expect(queryKeys.projects.detail("p1")).toEqual(["projects", "p1"]);
  });

  it("nests processing job keys", () => {
    expect(queryKeys.processing.jobs()).toEqual([
      "processing",
      "jobs",
      undefined,
    ]);
    expect(queryKeys.processing.job("j1")).toEqual([
      "processing",
      "job",
      "j1",
    ]);
  });

  it("nests scene results under their project", () => {
    expect(queryKeys.results.byProject("p1")).toEqual(["results", "p1"]);
    expect(queryKeys.results.scene("p1", "s1")).toEqual([
      "results",
      "p1",
      "scene",
      "s1",
    ]);
  });
});
