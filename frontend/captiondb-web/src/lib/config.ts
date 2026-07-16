// ============================================================
// Application Configuration
// ============================================================
// All environment variables are read here — never in components.
// Use next.config.ts to expose NEXT_PUBLIC_* vars.
// ============================================================

export const API_CONFIG = {
  baseUrl:
    // process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://captiondb.onrender.com/api/v1",
  timeout: Number(process.env.NEXT_PUBLIC_API_TIMEOUT ?? 10_000),
  retries: 2,
} as const;

export const APP_CONFIG = {
  name: "CaptionDB",
  description: "AI-powered video captioning and analysis platform",
  version: process.env.NEXT_PUBLIC_APP_VERSION ?? "0.1.0",
  environment: process.env.NODE_ENV,
  isProduction: process.env.NODE_ENV === "production",
  isDevelopment: process.env.NODE_ENV === "development",
} as const;

export const AUTH_CONFIG = {
  /** Storage key for the access token in sessionStorage */
  accessTokenKey: "captiondb:access_token",
  /** Storage key for the session ID */
  sessionIdKey: "captiondb:session_id",
  /** How long before token expiry to proactively refresh (ms) */
  refreshThresholdMs: 60_000,
  /** Redirect after login when no returnUrl is present */
  defaultPostLoginPath: "/dashboard",
  /** Redirect unauthenticated users to */
  loginPath: "/auth/login",
} as const;

export const QUERY_CONFIG = {
  /** Stale time for most queries — 30s */
  staleTime: 30_000,
  /** Cache time after unmount — 5 min */
  gcTime: 5 * 60_000,
  /** Retry failed queries this many times (client-side network errors only) */
  retry: 1,
} as const;
