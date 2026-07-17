"""
Admin module schemas.
Response/request models for the admin console endpoints.
"""
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.domain.models.video import CaptionTone, VideoStatus
from app.api.schemas.upload import VideoMetadataSchema


# ── Auth ─────────────────────────────────────────────────────────

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    expires_in: Optional[int] = None
    error: Optional[str] = None


# ── Overview ─────────────────────────────────────────────────────

class DailyRequestCount(BaseModel):
    date: str  # ISO date (YYYY-MM-DD)
    received: int
    completed: int


class AdminOverviewResponse(BaseModel):
    requests_received: int
    requests_accomplished: int
    requests_failed: int
    requests_processing: int
    requests_idle: int
    total_scenes: int
    total_captions: int
    avg_processing_seconds: float
    total_storage_bytes: int
    daily_requests: List[DailyRequestCount]
    status_breakdown: Dict[str, int]


# ── Requests list / inspector ────────────────────────────────────

class AdminRequestItem(BaseModel):
    """One row of the admin requests table: data provided + results generated."""
    id: str
    project_name: str
    original_filename: str
    status: VideoStatus
    metadata: Optional[VideoMetadataSchema] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_seconds: Optional[float] = None
    error_message: Optional[str] = None
    progress_percent: float = 0.0
    current_stage: Optional[str] = None
    scenes_count: int
    captions_count: int


class AdminRequestListResponse(BaseModel):
    data: List[AdminRequestItem]
    total: int


class AdminSceneDetail(BaseModel):
    scene_id: str
    seconds_start: float
    seconds_end: float
    title: Optional[str] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    tags: List[str] = []
    objects: List[str] = []
    activities: List[str] = []
    colors: List[str] = []
    ocr_text: Optional[str] = None
    captions: Dict[CaptionTone, str] = {}


class AdminRequestDetailResponse(BaseModel):
    """Full inspector payload: everything provided and everything generated."""
    request: AdminRequestItem
    scenes: List[AdminSceneDetail]
