// ============================================================
// App-wide route constants
// ============================================================
// Single source of truth — never hardcode paths in components.
// ============================================================

export const ROUTES = {
  // Public
  home: "/",
  // Auth
  auth: {
    login: "/auth/login",
    register: "/auth/register",
    forgotPassword: "/auth/forgot-password",
    oauthCallback: "/auth/callback",
  },
  // Protected
  dashboard: "/dashboard",
  projects: {
    list: "/dashboard/projects",
    create: "/dashboard/projects/new",
    detail: (id: string) => `/dashboard/projects/${id}`,
  },
  sessions: "/dashboard/sessions",
  settings: {
    profile: "/dashboard/settings/profile",
    security: "/dashboard/settings/security",
    identities: "/dashboard/settings/identities",
  },
  // Error
  notFound: "/not-found",
  unauthorized: "/unauthorized",
} as const;
