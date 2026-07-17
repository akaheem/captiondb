/**
 * CaptionDB API client.
 * Typed against the FastAPI backend at /api/v1 — the backend is the
 * source of truth; these types mirror its Pydantic schemas exactly.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const V1 = `${API_BASE}/api/v1`;

// ── Types (mirroring backend schemas) ─────────────────────────────

export type VideoStatus = "Idle" | "Queued" | "Processing" | "Completed" | "Failed";

export type CaptionTone =
  | "formal"
  | "sarcastic"
  | "humorousTech"
  | "humorousNonTech"
  | "audio"
  | "none";

export interface VideoDimensions {
  width: number;
  height: number;
}

export interface VideoMetadata {
  size_bytes: number;
  duration_seconds: number;
  fps: number;
  codec: string;
  resolution: string;
  dimensions?: VideoDimensions | null;
  format: string;
}

export interface Scene {
  scene_id: string;
  seconds_start: number;
  seconds_end: number;
  title?: string | null;
  summary?: string | null;
  transcript?: string | null;
  tags: string[];
}

export interface Project {
  id: string;
  project_name: string;
  status: VideoStatus;
  metadata?: VideoMetadata | null;
  created_at: string;
  updated_at: string;
  scenes: Scene[];
}

export interface ProjectListResponse {
  data: Project[];
  total: number;
}

export interface UploadResponse {
  success: boolean;
  video_id?: string | null;
  project_name?: string | null;
  status?: VideoStatus | null;
  metadata?: VideoMetadata | null;
  errors?: string[] | null;
}

export interface ProcessingStatus {
  status: VideoStatus;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
}

export interface ProcessingProgress {
  progress_percent: number;
  current_stage?: string | null;
}

export interface SceneCaptions {
  scene_id: string;
  seconds_start: number;
  seconds_end: number;
  captions: Partial<Record<CaptionTone, string>>;
}

export interface ProjectSummary {
  total_scenes: number;
  successful_scenes: number;
  processing_duration_seconds: number;
  total_captions: number;
  status: VideoStatus;
}

// Admin types
export interface AdminOverview {
  requests_received: number;
  requests_accomplished: number;
  requests_failed: number;
  requests_processing: number;
  requests_idle: number;
  total_scenes: number;
  total_captions: number;
  avg_processing_seconds: number;
  total_storage_bytes: number;
  daily_requests: { date: string; received: number; completed: number }[];
  status_breakdown: Record<string, number>;
}

export interface AdminRequestItem {
  id: string;
  project_name: string;
  original_filename: string;
  status: VideoStatus;
  metadata?: VideoMetadata | null;
  created_at: string;
  updated_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  processing_seconds?: number | null;
  error_message?: string | null;
  progress_percent: number;
  current_stage?: string | null;
  scenes_count: number;
  captions_count: number;
}

export interface AdminSceneDetail extends Scene {
  objects: string[];
  activities: string[];
  colors: string[];
  ocr_text?: string | null;
  captions: Partial<Record<CaptionTone, string>>;
}

export interface AdminRequestDetail {
  request: AdminRequestItem;
  scenes: AdminSceneDetail[];
}

export interface HealthLive {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  uptime_seconds: number;
}

// ── Errors ────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public body?: unknown,
  ) {
    super(message);
  }
}

async function parseError(res: Response): Promise<ApiError> {
  let message = `Request failed (${res.status})`;
  let body: unknown;
  try {
    body = await res.json();
    const b = body as Record<string, unknown>;
    if (typeof b.message === "string") message = b.message;
    else if (typeof b.detail === "string") message = b.detail;
    else if (b.detail && typeof b.detail === "object") {
      const d = b.detail as Record<string, unknown>;
      if (typeof d.message === "string") message = d.message;
      else message = JSON.stringify(b.detail);
    }
  } catch {
    /* non-JSON body */
  }
  return new ApiError(res.status, message, body);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${V1}${path}`, init);
  if (!res.ok) throw await parseError(res);
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── System ────────────────────────────────────────────────────────

export const getHealth = () => request<HealthLive>("/health/live");

// ── Upload ────────────────────────────────────────────────────────

export async function uploadVideo(
  projectName: string,
  file: File,
): Promise<UploadResponse> {
  const form = new FormData();
  form.append("project_name", projectName);
  form.append("file", file);
  const res = await fetch(`${V1}/upload/`, { method: "POST", body: form });
  if (!res.ok) throw await parseError(res);
  return res.json();
}

// ── Projects ──────────────────────────────────────────────────────

export const listProjects = (params?: {
  limit?: number;
  offset?: number;
  sort_by?: string;
  status?: VideoStatus;
}) => {
  const q = new URLSearchParams();
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  if (params?.sort_by) q.set("sort_by", params.sort_by);
  if (params?.status) q.set("status", params.status);
  const qs = q.toString();
  return request<ProjectListResponse>(`/projects/${qs ? `?${qs}` : ""}`);
};

export const getProject = (id: string) => request<Project>(`/projects/${id}`);

export const deleteProject = (id: string) =>
  request<void>(`/projects/${id}`, { method: "DELETE" });

export const duplicateProject = (id: string) =>
  request<Project>(`/projects/${id}/duplicate`, { method: "POST" });

export const processProject = (id: string) =>
  request<{ project_id: string; status: VideoStatus; message: string }>(
    `/projects/${id}/process`,
    { method: "POST" },
  );

export const getProjectStatus = (id: string) =>
  request<ProcessingStatus>(`/projects/${id}/status`);

export const getProjectProgress = (id: string) =>
  request<ProcessingProgress>(`/projects/${id}/progress`);

export const getProjectScenes = (id: string) =>
  request<{ data: Scene[]; total: number }>(`/projects/${id}/scenes`);

export const getProjectCaptions = (id: string) =>
  request<{ data: SceneCaptions[]; total: number }>(`/projects/${id}/captions`);

export const getProjectSummary = (id: string) =>
  request<ProjectSummary>(`/projects/${id}/summary`);

// ── Admin ─────────────────────────────────────────────────────────

const ADMIN_TOKEN_KEY = "captiondb_admin_token";

export function getAdminToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ADMIN_TOKEN_KEY);
}

export function setAdminToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem(ADMIN_TOKEN_KEY, token);
  else localStorage.removeItem(ADMIN_TOKEN_KEY);
}

function adminHeaders(): HeadersInit {
  const token = getAdminToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const adminLogin = (email: string, password: string) =>
  request<{ success: boolean; token?: string; expires_in?: number }>(
    "/admin/login",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    },
  );

export const adminMe = () =>
  request<{ email: string; role: string }>("/admin/me", {
    headers: adminHeaders(),
  });

export const adminOverview = (days = 7) =>
  request<AdminOverview>(`/admin/overview?days=${days}`, {
    headers: adminHeaders(),
  });

export const adminListRequests = (params?: {
  limit?: number;
  offset?: number;
  status?: VideoStatus;
}) => {
  const q = new URLSearchParams();
  if (params?.limit) q.set("limit", String(params.limit));
  if (params?.offset) q.set("offset", String(params.offset));
  if (params?.status) q.set("status", params.status);
  const qs = q.toString();
  return request<{ data: AdminRequestItem[]; total: number }>(
    `/admin/requests${qs ? `?${qs}` : ""}`,
    { headers: adminHeaders() },
  );
};

export const adminRequestDetail = (id: string) =>
  request<AdminRequestDetail>(`/admin/requests/${id}`, {
    headers: adminHeaders(),
  });

export const adminDeleteRequest = (id: string) =>
  request<void>(`/admin/requests/${id}`, {
    method: "DELETE",
    headers: adminHeaders(),
  });

// ── User auth (backend providers are stubbed; endpoints wired for
//    when they come online) ────────────────────────────────────────

export interface UserSchema {
  user_id: string;
  email: string;
  username: string;
  display_name?: string | null;
  avatar_url?: string | null;
  role: string;
  status: string;
  verified: boolean;
  identities: {
    provider: string;
    oauth_provider?: string | null;
    provider_id: string;
    linked_at?: string | null;
  }[];
}

const USER_TOKEN_KEY = "captiondb_token";

export function getUserToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(USER_TOKEN_KEY);
}

export function setUserToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem(USER_TOKEN_KEY, token);
  else localStorage.removeItem(USER_TOKEN_KEY);
}

function userHeaders(): HeadersInit {
  const token = getUserToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const login = (email: string, password: string) =>
  request<{
    success: boolean;
    user?: UserSchema;
    tokens?: { access_token: string };
    error?: { code: string; message: string };
  }>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

export const register = (email: string, username: string, password: string) =>
  request<{
    success: boolean;
    user?: UserSchema;
    requires_verification?: boolean;
    error?: { code: string; message: string };
  }>("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password }),
  });

export const me = () =>
  request<{ user: UserSchema }>("/auth/me", { headers: userHeaders() });

export const logout = () =>
  request<{ success: boolean }>("/auth/logout", {
    method: "POST",
    headers: { ...userHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });

export const listSessions = () =>
  request<{
    sessions: {
      session_id: string;
      user_id: string;
      created_at: string;
      last_seen_at?: string | null;
      ip_address?: string | null;
      user_agent?: string | null;
      is_expired: boolean;
    }[];
    total: number;
  }>("/auth/sessions", { headers: userHeaders() });

export const revokeSession = (sessionId: string) =>
  request<{ success: boolean }>(`/auth/sessions/${sessionId}`, {
    method: "DELETE",
    headers: userHeaders(),
  });

export const revokeAllSessions = () =>
  request<{ success: boolean; revoked_count?: number }>("/auth/sessions", {
    method: "DELETE",
    headers: userHeaders(),
  });

// ── Formatting helpers ────────────────────────────────────────────

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.round(seconds % 60);
  if (h > 0)
    return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function formatBytes(bytes: number): string {
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
  if (bytes >= 1024 ** 2) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${bytes} B`;
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} day${days > 1 ? "s" : ""} ago`;
  const weeks = Math.floor(days / 7);
  return `${weeks} week${weeks > 1 ? "s" : ""} ago`;
}

export const TONE_LABELS: Record<string, { label: string; emoji: string }> = {
  formal: { label: "Formal", emoji: "🏛" },
  sarcastic: { label: "Sarcastic", emoji: "😏" },
  humorousTech: { label: "Humorous Tech", emoji: "🤓" },
  humorousNonTech: { label: "Humorous", emoji: "😂" },
  audio: { label: "Audio", emoji: "🔊" },
  none: { label: "Plain", emoji: "📝" },
};
