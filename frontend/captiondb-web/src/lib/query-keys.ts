// ============================================================
// React Query Keys — centralized query key factory
// ============================================================
// All query keys live here so invalidation is predictable.
// ============================================================

export const queryKeys = {
  auth: {
    all: ["auth"] as const,
    sessions: () => [...queryKeys.auth.all, "sessions"] as const,
    session: (id: string) => [...queryKeys.auth.sessions(), id] as const,
  },
  user: {
    all: ["user"] as const,
    me: () => [...queryKeys.user.all, "me"] as const,
    byId: (id: string) => [...queryKeys.user.all, id] as const,
  },
  projects: {
    all: ["projects"] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.projects.all, "list", filters] as const,
    detail: (id: string) => [...queryKeys.projects.all, id] as const,
  },
  processing: {
    all: ["processing"] as const,
    jobs: (filters?: Record<string, unknown>) =>
      [...queryKeys.processing.all, "jobs", filters] as const,
    job: (id: string) => [...queryKeys.processing.all, "job", id] as const,
  },
  results: {
    all: ["results"] as const,
    byProject: (projectId: string) =>
      [...queryKeys.results.all, projectId] as const,
    scene: (projectId: string, sceneId: string) =>
      [...queryKeys.results.byProject(projectId), "scene", sceneId] as const,
  },
} as const;
