// ============================================================
// Global TypeScript Types — API Contract
// ============================================================
// These types mirror the backend DTOs exactly.
// Do NOT add frontend-specific fields here.
// ============================================================

// ─── Error types ────────────────────────────────────────────────────────────

export enum ApiErrorCode {
  // General
  INTERNAL_ERROR = "INTERNAL_ERROR",
  VALIDATION_ERROR = "VALIDATION_ERROR",
  NOT_FOUND = "NOT_FOUND",
  CONFLICT = "CONFLICT",
  // Auth
  AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR",
  INVALID_CREDENTIALS = "INVALID_CREDENTIALS",
  ACCOUNT_NOT_ACTIVE = "ACCOUNT_NOT_ACTIVE",
  TOKEN_EXPIRED = "TOKEN_EXPIRED",
  OAUTH_PROVIDER_ERROR = "OAUTH_PROVIDER_ERROR",
  IDENTITY_ALREADY_LINKED = "IDENTITY_ALREADY_LINKED",
  IDENTITY_NOT_FOUND = "IDENTITY_NOT_FOUND",
  // Network (client-only)
  NETWORK_ERROR = "NETWORK_ERROR",
  TIMEOUT = "TIMEOUT",
}

export interface ApiError {
  code: ApiErrorCode;
  message: string;
  details: Record<string, unknown>;
  status: number;
}

// ─── Auth types ──────────────────────────────────────────────────────────────

export type OAuthProvider =
  | "google"
  | "github"
  | "apple"
  | "microsoft"
  | "twitter";

export type IdentityProvider = "email" | "oauth";

export type AccountStatus =
  | "active"
  | "suspended"
  | "pending_verification";

export type UserRole = "user" | "admin";

export interface UserIdentityDTO {
  provider: IdentityProvider;
  oauth_provider: OAuthProvider | null;
  provider_id: string;
  linked_at: string; // ISO-8601
}

export interface UserDTO {
  user_id: string;
  email: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  role: UserRole;
  status: AccountStatus;
  verified: boolean;
  identities: UserIdentityDTO[];
}

export interface TokenDTO {
  access_token: string;
  token_type: string;
  expires_in: number | null;
  refresh_token: string | null;
}

export interface SessionDTO {
  session_id: string;
  user_id: string;
  created_at: string; // ISO-8601
}

// ─── Auth request types ───────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface OAuthBeginRequest {
  provider: OAuthProvider;
  state: string;
  redirect_uri: string;
}

export interface OAuthCompleteRequest {
  provider: OAuthProvider;
  code: string;
  redirect_uri: string;
}

// ─── Auth response types ──────────────────────────────────────────────────────

export interface LoginResponse {
  success: boolean;
  user?: UserDTO;
  tokens?: TokenDTO;
  session?: SessionDTO;
  error?: { code: string; message: string; details: Record<string, unknown> };
}

export interface RegisterResponse {
  success: boolean;
  user?: UserDTO;
  requires_verification: boolean;
  error?: { code: string; message: string; details: Record<string, unknown> };
}

export interface OAuthLoginResponse {
  success: boolean;
  authorization_url?: string;
  error?: { code: string; message: string };
}

export interface OAuthCompleteResponse {
  success: boolean;
  user?: UserDTO;
  tokens?: TokenDTO;
  session?: SessionDTO;
  is_new_user: boolean;
  error?: { code: string; message: string };
}

export interface SessionListResponse {
  sessions: SessionInfoDTO[];
  total: number;
}

export interface SessionInfoDTO {
  session_id: string;
  user_id: string;
  created_at: string;
  last_seen_at: string | null;
  ip_address: string | null;
  user_agent: string | null;
  is_expired: boolean;
}

// ─── Project types ────────────────────────────────────────────────────────────

export interface VideoDimensionsDTO {
  width: number;
  height: number;
}

export interface VideoMetadataDTO {
  size_bytes: number;
  duration_seconds: number;
  fps: number;
  codec: string;
  resolution: string;
  dimensions: VideoDimensionsDTO;
  format: string;
}

export interface CaptionDTO {
  text: string;
  start: number;
  end: number;
}

export interface SceneDTO {
  scene_id: string;
  seconds_start: number;
  seconds_end: number;
  title: string;
  summary: string;
  transcript: string;
  tags: string[];
  captions?: CaptionDTO[];
}

export type VideoStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface ProjectDTO {
  id: string;
  project_name: string;
  status: VideoStatus;
  metadata?: VideoMetadataDTO;
  created_at: string;
  updated_at: string;
  scenes?: SceneDTO[];
}

export interface ProjectListResponse {
  data: ProjectDTO[];
  total: number;
}

// ─── Processing / AI Job types ────────────────────────────────────────────────
// Mirrors the backend TaskResponse DTO (app/api/schemas/task.py) plus the
// list-wrapper and monitor-oriented fields (ETA, logs) exposed by the
// /v1/processing/jobs endpoints.

export type ProcessingJobStatus =
  | "QUEUED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "RETRYING";

export type ProcessingLogLevel = "debug" | "info" | "warning" | "error";

export interface ProcessingLogEntryDTO {
  timestamp: string; // ISO-8601
  level: ProcessingLogLevel;
  message: string;
}

export interface ProcessingJobDTO {
  /** Backend task identifier. */
  task_id: string;
  /** Owning project, when the job is tied to one. */
  project_id: string | null;
  /** Human-readable project label, when the backend joins it in. */
  project_name?: string | null;
  status: ProcessingJobStatus;
  /** Percentage complete, 0–100. */
  progress: number;
  /** Current pipeline stage, e.g. "transcribing", "captioning". */
  current_stage: string | null;
  // Timestamps (ISO-8601)
  created_at: string | null;
  started_at: string | null;
  updated_at: string;
  completed_at: string | null;
  /** Estimated completion time, when the backend can predict it. */
  estimated_completion_at?: string | null;
  duration_seconds?: number | null;
  retry_count: number;
  error_message: string | null;
  /** Recent log lines for live monitoring, newest last. */
  logs?: ProcessingLogEntryDTO[];
}

export interface ProcessingJobListResponse {
  data: ProcessingJobDTO[];
  total: number;
}

// ─── Results / Scene Explorer types ──────────────────────────────────────────
// Mirrors the backend results endpoints:
//   GET /v1/projects/{id}/scenes   → SceneListResponse
//   GET /v1/projects/{id}/captions → CaptionListResponse
//   GET /v1/projects/{id}/summary  → ProjectSummaryDTO
// Vision-analysis fields (objects, activities, colors, OCR, safety, confidence)
// and thumbnails/token-usage exist in the AI domain model but are NOT currently
// exposed by the API — they are modeled as optional here so the UI can display
// "Not available" and light up automatically if the backend adds them later.

/** Caption tones supported by the backend (app/domain/models/video.py). */
export type CaptionTone =
  | "formal"
  | "sarcastic"
  | "humorousTech"
  | "humorousNonTech"
  | "audio"
  | "none";

/** Map of tone → generated caption text, as returned by /captions. */
export type CaptionSet = Partial<Record<CaptionTone, string>>;

/** Raw scene as returned by GET /scenes (SceneSchema). */
export interface SceneListResponse {
  data: SceneDTO[];
  total: number;
}

/** Per-scene captions as returned by GET /captions (CaptionResponse). */
export interface SceneCaptionsDTO {
  scene_id: string;
  seconds_start: number;
  seconds_end: number;
  captions: CaptionSet;
}

export interface CaptionListResponse {
  data: SceneCaptionsDTO[];
  total: number;
}

/** GET /summary (ProjectSummaryResponse). */
export interface ProjectSummaryDTO {
  total_scenes: number;
  successful_scenes: number;
  processing_duration_seconds: number;
  total_captions: number;
  status: VideoStatus;
  /** Not returned by the API today; present for forward-compatibility. */
  token_usage?: number | null;
}

/**
 * A scene merged with its captions and (when available) vision analysis.
 * This is the primary unit the Scene Explorer renders. Optional fields are
 * absent until the backend exposes them — the UI degrades gracefully.
 */
export interface SceneResultDTO {
  scene_id: string;
  seconds_start: number;
  seconds_end: number;
  title: string | null;
  summary: string | null;
  transcript: string | null;
  tags: string[];
  captions: CaptionSet;
  // Vision analysis (not yet exposed by the API → "Not available")
  thumbnail_url?: string | null;
  objects?: string[];
  people?: string[];
  activities?: string[];
  environment?: string | null;
  mood?: string | null;
  dominant_colors?: string[];
  ocr_text?: string | null;
  safety_flags?: string[];
  confidence?: number | null;
}

/** Merged, ready-to-render results for a project. */
export interface ProjectResultsData {
  scenes: SceneResultDTO[];
  summary: ProjectSummaryDTO | null;
}

// ─── Upload types ─────────────────────────────────────────────────────────────

export interface UploadResponse {
  success: boolean;
  video_id: string;
  project_name: string;
  status: VideoStatus;
  metadata?: VideoMetadataDTO;
  errors?: string[];
}
