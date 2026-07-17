"""
Admin endpoints.

Provides the admin console API: login, platform overview statistics,
the full requests table (data provided + results generated), and a
per-request inspector. All data is computed from the existing Video
aggregate via ProjectService — no separate metrics store required.
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.schemas.upload import VideoMetadataSchema, VideoDimensionsSchema
from app.api.v1.admin.auth import (
    create_admin_token,
    require_admin,
    verify_admin_password,
)
from app.api.v1.admin.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminOverviewResponse,
    AdminRequestDetailResponse,
    AdminRequestItem,
    AdminRequestListResponse,
    AdminSceneDetail,
    DailyRequestCount,
)
from app.core.config import get_settings
from app.core.exceptions import NotFoundException
from app.dependencies.services import get_project_service
from app.domain.models.video import Video, VideoStatus
from app.services.project import ProjectService

router = APIRouter()


# ── Mapping helpers ──────────────────────────────────────────────

def _map_metadata(video: Video) -> Optional[VideoMetadataSchema]:
    if not video.metadata:
        return None
    return VideoMetadataSchema(
        size_bytes=video.metadata.size_bytes,
        duration_seconds=video.metadata.duration_seconds,
        fps=video.metadata.fps,
        codec=video.metadata.codec,
        resolution=video.metadata.resolution,
        dimensions=VideoDimensionsSchema(
            width=video.metadata.dimensions.width,
            height=video.metadata.dimensions.height,
        ) if video.metadata.dimensions else None,
        format=video.metadata.format,
    )


def _processing_seconds(video: Video) -> Optional[float]:
    if video.state.started_at and video.state.completed_at:
        return (video.state.completed_at - video.state.started_at).total_seconds()
    return None


def _map_request_item(video: Video) -> AdminRequestItem:
    return AdminRequestItem(
        id=video.id,
        project_name=video.project_name,
        original_filename=video.original_filename,
        status=video.state.status,
        metadata=_map_metadata(video),
        created_at=video.created_at,
        updated_at=video.updated_at,
        started_at=video.state.started_at,
        completed_at=video.state.completed_at,
        processing_seconds=_processing_seconds(video),
        error_message=video.state.error_message,
        progress_percent=video.state.progress_percent,
        current_stage=video.state.current_stage,
        scenes_count=len(video.scenes),
        captions_count=sum(len(s.captions) for s in video.scenes),
    )


# ── Auth ─────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=AdminLoginResponse,
    summary="Admin login",
    description="Authenticates the platform administrator against env-configured credentials.",
)
async def admin_login(payload: AdminLoginRequest) -> AdminLoginResponse:
    settings = get_settings()
    admin = settings.admin

    if not admin.email or not admin.password_hash:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "ADMIN_NOT_CONFIGURED", "message": "Admin credentials are not configured."},
        )

    email_ok = payload.email.lower() == admin.email.lower()
    password_ok = verify_admin_password(payload.password, admin.password_hash)
    if not (email_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid admin email or password."},
        )

    expires_in = admin.token_expire_minutes * 60
    token = create_admin_token(admin.email, expires_in)
    return AdminLoginResponse(success=True, token=token, expires_in=expires_in)


@router.get(
    "/me",
    summary="Verify admin session",
    description="Validates the current admin token.",
)
async def admin_me(admin_email: str = Depends(require_admin)) -> dict:
    return {"email": admin_email, "role": "admin"}


# ── Overview ─────────────────────────────────────────────────────

@router.get(
    "/overview",
    response_model=AdminOverviewResponse,
    summary="Platform overview statistics",
    description="Aggregated request/scene/caption statistics across all projects.",
)
async def admin_overview(
    days: int = Query(7, ge=1, le=90, description="Window for the daily requests chart"),
    admin_email: str = Depends(require_admin),
    project_service: ProjectService = Depends(get_project_service),
) -> AdminOverviewResponse:
    videos, total = await project_service.get_all_projects(limit=1000, offset=0)

    status_counts = Counter(v.state.status for v in videos)
    durations = [d for v in videos if (d := _processing_seconds(v)) is not None]

    # Daily received/completed counts for the chart window
    now = datetime.now(timezone.utc)
    window_start = (now - timedelta(days=days - 1)).date()
    received_by_day: dict = defaultdict(int)
    completed_by_day: dict = defaultdict(int)
    for v in videos:
        created_day = v.created_at.date()
        if created_day >= window_start:
            received_by_day[created_day] += 1
        if v.state.completed_at and v.state.completed_at.date() >= window_start:
            completed_by_day[v.state.completed_at.date()] += 1

    daily = [
        DailyRequestCount(
            date=(window_start + timedelta(days=i)).isoformat(),
            received=received_by_day.get(window_start + timedelta(days=i), 0),
            completed=completed_by_day.get(window_start + timedelta(days=i), 0),
        )
        for i in range(days)
    ]

    return AdminOverviewResponse(
        requests_received=total,
        requests_accomplished=status_counts.get(VideoStatus.COMPLETED, 0),
        requests_failed=status_counts.get(VideoStatus.FAILED, 0),
        requests_processing=status_counts.get(VideoStatus.PROCESSING, 0)
        + status_counts.get(VideoStatus.QUEUED, 0),
        requests_idle=status_counts.get(VideoStatus.IDLE, 0),
        total_scenes=sum(len(v.scenes) for v in videos),
        total_captions=sum(len(s.captions) for v in videos for s in v.scenes),
        avg_processing_seconds=sum(durations) / len(durations) if durations else 0.0,
        total_storage_bytes=sum(v.metadata.size_bytes for v in videos if v.metadata),
        daily_requests=daily,
        status_breakdown={s.value: c for s, c in status_counts.items()},
    )


# ── Requests table + inspector ───────────────────────────────────

@router.get(
    "/requests",
    response_model=AdminRequestListResponse,
    summary="List all requests",
    description="All requests with data provided and results generated, newest first.",
)
async def admin_list_requests(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status_filter: Optional[VideoStatus] = Query(None, alias="status"),
    admin_email: str = Depends(require_admin),
    project_service: ProjectService = Depends(get_project_service),
) -> AdminRequestListResponse:
    videos, total = await project_service.get_all_projects(
        limit=limit, offset=offset, sort_by="created_at", status=status_filter
    )
    return AdminRequestListResponse(
        data=[_map_request_item(v) for v in videos],
        total=total,
    )


@router.get(
    "/requests/{request_id}",
    response_model=AdminRequestDetailResponse,
    summary="Inspect a request",
    description="Full detail of one request: submitted data plus every generated scene and caption.",
)
async def admin_request_detail(
    request_id: str = Path(...),
    admin_email: str = Depends(require_admin),
    project_service: ProjectService = Depends(get_project_service),
) -> AdminRequestDetailResponse:
    try:
        video = await project_service.get_project_by_id(request_id)
    except (NotFoundException, ValueError):
        # ValueError: request_id is not a valid UUID — treat as not found.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request with ID {request_id} not found.",
        )

    scenes = [
        AdminSceneDetail(
            scene_id=s.scene_id,
            seconds_start=s.seconds_start,
            seconds_end=s.seconds_end,
            title=s.title,
            summary=s.summary,
            transcript=s.transcript,
            tags=s.tags,
            objects=s.objects,
            activities=s.activities,
            colors=s.colors,
            ocr_text=s.ocr_text,
            captions=s.captions,
        )
        for s in video.scenes
    ]
    return AdminRequestDetailResponse(request=_map_request_item(video), scenes=scenes)


@router.delete(
    "/requests/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a request",
    description="Deletes a request (project) and all of its associated data.",
)
async def admin_delete_request(
    request_id: str = Path(...),
    admin_email: str = Depends(require_admin),
    project_service: ProjectService = Depends(get_project_service),
) -> None:
    try:
        await project_service.delete_project(request_id)
    except (NotFoundException, ValueError):
        # ValueError: request_id is not a valid UUID — treat as not found.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request with ID {request_id} not found.",
        )
