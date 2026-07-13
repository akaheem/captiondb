// ============================================================
// Token Storage
// ============================================================
// Wraps sessionStorage access with typed helpers.
//
// Security note:
//   - Access tokens are stored in sessionStorage (not localStorage)
//     so they do NOT survive across browser tabs/sessions.
//   - Never store tokens in cookies without HttpOnly + SameSite=Strict.
//   - XSS exposure is mitigated by Content-Security-Policy headers
//     (configured in next.config.ts) and avoiding eval()/innerHTML.
// ============================================================

import { AUTH_CONFIG } from "@/lib/config";

export const TokenStorage = {
  /** Retrieve the access token — null when not authenticated. */
  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem(AUTH_CONFIG.accessTokenKey);
  },

  setAccessToken(token: string): void {
    if (typeof window === "undefined") return;
    sessionStorage.setItem(AUTH_CONFIG.accessTokenKey, token);
  },

  getSessionId(): string | null {
    if (typeof window === "undefined") return null;
    return sessionStorage.getItem(AUTH_CONFIG.sessionIdKey);
  },

  setSessionId(sessionId: string): void {
    if (typeof window === "undefined") return;
    sessionStorage.setItem(AUTH_CONFIG.sessionIdKey, sessionId);
  },

  /** Clear all auth-related storage on logout. */
  clear(): void {
    if (typeof window === "undefined") return;
    sessionStorage.removeItem(AUTH_CONFIG.accessTokenKey);
    sessionStorage.removeItem(AUTH_CONFIG.sessionIdKey);
  },

  /** True when a token exists in storage. */
  isAuthenticated(): boolean {
    return Boolean(TokenStorage.getAccessToken());
  },
} as const;
