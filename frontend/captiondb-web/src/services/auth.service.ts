// ============================================================
// Authentication API Service
// ============================================================
// The ONLY place that calls auth endpoints.
// Pages/components call hooks that call this service.
// ============================================================

import { apiClient } from "@/lib/api-client";
import type {
  LoginRequest,
  LoginResponse,
  OAuthBeginRequest,
  OAuthCompleteRequest,
  OAuthCompleteResponse,
  OAuthLoginResponse,
  RegisterRequest,
  RegisterResponse,
  SessionListResponse,
  UserDTO,
} from "@/types/api";

const AUTH_BASE = "/v1/auth";

export const authService = {
  /**
   * Email + password login.
   * On success, caller is responsible for persisting the token via TokenStorage.
   */
  async login(payload: LoginRequest): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>(`${AUTH_BASE}/login`, payload);
  },

  /** Register a new account with email + password. */
  async register(payload: RegisterRequest): Promise<RegisterResponse> {
    return apiClient.post<RegisterResponse>(`${AUTH_BASE}/register`, payload);
  },

  /** Get the authorization URL for an OAuth provider. */
  async beginOAuthLogin(payload: OAuthBeginRequest): Promise<OAuthLoginResponse> {
    return apiClient.post<OAuthLoginResponse>(
      `${AUTH_BASE}/oauth/${payload.provider}/begin`,
      { state: payload.state, redirect_uri: payload.redirect_uri }
    );
  },

  /** Exchange OAuth code for tokens after redirect. */
  async completeOAuthLogin(
    payload: OAuthCompleteRequest
  ): Promise<OAuthCompleteResponse> {
    const params = new URLSearchParams({
      code: payload.code,
      state: (payload as any).state || "ignored", // The backend needs state. The frontend type doesn't have it explicitly right now, so we pass what we have
      redirect_uri: payload.redirect_uri,
    });
    return apiClient.get<OAuthCompleteResponse>(
      `${AUTH_BASE}/oauth/${payload.provider}/callback?${params.toString()}`
    );
  },

  /** Refresh the access token using the current session. */
  async refreshSession(sessionId: string | null): Promise<LoginResponse> {
    return apiClient.post<LoginResponse>(`${AUTH_BASE}/refresh`, {
      session_id: sessionId,
    });
  },

  /** Logout — revokes the current token and session. */
  async logout(sessionId: string | null): Promise<void> {
    await apiClient.post<void>(`${AUTH_BASE}/logout`, { session_id: sessionId });
  },

  /** Get all active sessions for the current user. */
  async listSessions(): Promise<SessionListResponse> {
    return apiClient.get<SessionListResponse>(`${AUTH_BASE}/sessions`);
  },

  /** Revoke a specific session. */
  async revokeSession(sessionId: string): Promise<void> {
    return apiClient.delete<void>(`${AUTH_BASE}/sessions/${sessionId}`);
  },

  /** Revoke ALL sessions for the current user. */
  async revokeAllSessions(): Promise<void> {
    return apiClient.delete<void>(`${AUTH_BASE}/sessions`);
  },

  async getMe(): Promise<{ user: UserDTO }> {
    return apiClient.get<{ user: UserDTO }>(`${AUTH_BASE}/me`);
  }
} as const;
