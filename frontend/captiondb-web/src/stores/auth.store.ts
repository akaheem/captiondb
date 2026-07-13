// ============================================================
// Auth Store — Zustand
// ============================================================
// Manages ONLY the authentication slice of global state.
// User data, session data, and loading/error states.
//
// Architectural constraint:
//   Stores call services.
//   Components call store actions.
//   Components NEVER call services directly.
// ============================================================

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { authService } from "@/services/auth.service";
import { TokenStorage } from "@/lib/token-storage";
import type { UserDTO } from "@/types/api";

// ─── State shape ─────────────────────────────────────────────────────────────

interface AuthState {
  // Data
  user: UserDTO | null;
  sessionId: string | null;
  isAuthenticated: boolean;
  // Status
  isLoading: boolean;
  isInitialized: boolean; // True after the initial auth-check on mount
  error: string | null;
}

// ─── Actions ─────────────────────────────────────────────────────────────────

interface AuthActions {
  login(email: string, password: string): Promise<void>;
  register(
    email: string,
    username: string,
    password: string
  ): Promise<{ requiresVerification: boolean }>;
  logout(): Promise<void>;
  initialize(): Promise<void>;
  setUser(user: UserDTO | null): void;
  clearError(): void;
}

type AuthStore = AuthState & AuthActions;

// ─── Initial state ────────────────────────────────────────────────────────────

const INITIAL_STATE: AuthState = {
  user: null,
  sessionId: null,
  isAuthenticated: false,
  isLoading: false,
  isInitialized: false,
  error: null,
};

// ─── Store ───────────────────────────────────────────────────────────────────

export const useAuthStore = create<AuthStore>()(
  devtools(
    (set, get) => ({
      ...INITIAL_STATE,

      /** Called once on app mount — rehydrates from stored token. */
      async initialize() {
        if (get().isInitialized) return;

        const hasToken = TokenStorage.isAuthenticated();
        if (!hasToken) {
          set({ isInitialized: true }, false, "auth/initialize:no-token");
          return;
        }

        set({ isLoading: true }, false, "auth/initialize:start");
        try {
          const sessionId = TokenStorage.getSessionId();
          const response = await authService.refreshSession(sessionId);

          if (response.success && response.user && response.tokens) {
            TokenStorage.setAccessToken(response.tokens.access_token);
            if (response.session) {
              TokenStorage.setSessionId(response.session.session_id);
            }
            set(
              {
                user: response.user,
                sessionId: response.session?.session_id ?? null,
                isAuthenticated: true,
                isInitialized: true,
                isLoading: false,
              },
              false,
              "auth/initialize:success"
            );
          } else {
            TokenStorage.clear();
            set(
              { ...INITIAL_STATE, isInitialized: true },
              false,
              "auth/initialize:failed"
            );
          }
        } catch {
          TokenStorage.clear();
          set(
            { ...INITIAL_STATE, isInitialized: true },
            false,
            "auth/initialize:error"
          );
        }
      },

      async login(email, password) {
        set({ isLoading: true, error: null }, false, "auth/login:start");
        try {
          const response = await authService.login({ email, password });
          if (!response.success || !response.user || !response.tokens) {
            throw new Error(response.error?.message ?? "Login failed");
          }
          TokenStorage.setAccessToken(response.tokens.access_token);
          if (response.session) {
            TokenStorage.setSessionId(response.session.session_id);
          }
          set(
            {
              user: response.user,
              sessionId: response.session?.session_id ?? null,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            },
            false,
            "auth/login:success"
          );
        } catch (err) {
          const message = err instanceof Error ? err.message : "Login failed";
          set({ isLoading: false, error: message }, false, "auth/login:error");
          throw err;
        }
      },

      async register(email, username, password) {
        set({ isLoading: true, error: null }, false, "auth/register:start");
        try {
          const response = await authService.register({
            email,
            username,
            password,
          });
          if (!response.success || !response.user) {
            throw new Error(response.error?.message ?? "Registration failed");
          }
          set({ isLoading: false }, false, "auth/register:success");
          return { requiresVerification: response.requires_verification };
        } catch (err) {
          const message =
            err instanceof Error ? err.message : "Registration failed";
          set(
            { isLoading: false, error: message },
            false,
            "auth/register:error"
          );
          throw err;
        }
      },

      async logout() {
        set({ isLoading: true }, false, "auth/logout:start");
        try {
          const currentSessionId = get().sessionId;
          await authService.logout(currentSessionId);
        } catch {
          // Logout is best-effort — always clear local state
        } finally {
          TokenStorage.clear();
          set(
            { ...INITIAL_STATE, isInitialized: true },
            false,
            "auth/logout:done"
          );
        }
      },

      setUser(user) {
        set(
          { user, isAuthenticated: Boolean(user) },
          false,
          "auth/setUser"
        );
      },

      clearError() {
        set({ error: null }, false, "auth/clearError");
      },
    }),
    { name: "AuthStore" }
  )
);

// ─── Selectors (memoised outside component) ───────────────────────────────────
export const selectUser = (s: AuthStore) => s.user;
export const selectIsAuthenticated = (s: AuthStore) => s.isAuthenticated;
export const selectIsLoading = (s: AuthStore) => s.isLoading;
export const selectAuthError = (s: AuthStore) => s.error;
export const selectIsInitialized = (s: AuthStore) => s.isInitialized;
