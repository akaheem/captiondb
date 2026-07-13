"""
Session Management Router — /api/v1/auth/sessions

Architecture constraint:
  Injects ONLY SessionManagementService and the CurrentUser from DI.
  No business logic. No token parsing. No direct DB calls.

Endpoints:
  GET    /auth/sessions              — list all sessions for the current user
  DELETE /auth/sessions/{session_id} — revoke one session
  DELETE /auth/sessions              — revoke all sessions (global logout)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from loguru import logger

from app.api.v1.auth.session_schemas import (
    RevokeSessionResponse,
    SessionInfoSchema,
    SessionListResponse,
)
from app.dependencies.services import get_current_user, get_session_management_service
from app.domain.models.auth import User
from app.services.session_management import SessionInfo, SessionManagementService
from app.core.exceptions import NotFoundException, CaptionDBException

router = APIRouter()

# Passed via ``openapi_extra`` — FastAPI route decorators do not accept a
# ``security=`` keyword; OpenAPI security requirements are injected this way.
_BEARER_SECURITY = {"security": [{"BearerAuth": []}]}


# ---------------------------------------------------------------------------
# Mapping helper
# ---------------------------------------------------------------------------

def _to_schema(info: SessionInfo) -> SessionInfoSchema:
    return SessionInfoSchema(
        session_id=info.session_id,
        user_id=info.user_id,
        created_at=info.created_at,
        last_seen_at=info.last_seen_at,
        ip_address=info.ip_address,
        user_agent=info.user_agent,
        is_expired=info.is_expired,
        metadata=info.metadata,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=SessionListResponse,
    summary="List active sessions",
    tags=["auth", "sessions"],
    openapi_extra=_BEARER_SECURITY,
    responses={
        200: {"description": "All sessions for the authenticated user."},
        401: {"description": "Not authenticated."},
    },
)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    session_mgmt: SessionManagementService = Depends(get_session_management_service),
) -> SessionListResponse:
    """
    Return all active (and recently expired) sessions for the current user.

    Use this endpoint to display connected devices in account settings.
    """
    logger.info(f"GET /sessions — user_id={current_user.id}")
    sessions = await session_mgmt.list_sessions(current_user.id)
    schemas = [_to_schema(s) for s in sessions]
    return SessionListResponse(sessions=schemas, total=len(schemas))


@router.delete(
    "/{session_id}",
    response_model=RevokeSessionResponse,
    summary="Revoke a single session",
    tags=["auth", "sessions"],
    openapi_extra=_BEARER_SECURITY,
    responses={
        200: {"description": "Session revoked."},
        401: {"description": "Not authenticated."},
        404: {"description": "Session not found or not owned by this user."},
    },
)
async def revoke_session(
    session_id: str = Path(..., description="Session ID to revoke."),
    current_user: User = Depends(get_current_user),
    session_mgmt: SessionManagementService = Depends(get_session_management_service),
) -> RevokeSessionResponse:
    """
    Terminate a single session by ID.

    The session must belong to the authenticated user.
    Silently succeeds if the session is already gone (idempotent).
    """
    logger.info(f"DELETE /sessions/{session_id} — user_id={current_user.id}")
    try:
        await session_mgmt.revoke_session(session_id, current_user.id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CaptionDBException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    return RevokeSessionResponse(success=True, session_id=session_id)


@router.delete(
    "",
    response_model=RevokeSessionResponse,
    summary="Revoke all sessions (global logout)",
    tags=["auth", "sessions"],
    openapi_extra=_BEARER_SECURITY,
    responses={
        200: {"description": "All sessions revoked."},
        401: {"description": "Not authenticated."},
    },
)
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
    session_mgmt: SessionManagementService = Depends(get_session_management_service),
) -> RevokeSessionResponse:
    """
    Sign out from every device simultaneously.

    This revokes ALL active sessions for the authenticated user.
    The current session will also be invalidated — the client must reauthenticate.
    """
    logger.info(f"DELETE /sessions (all) — user_id={current_user.id}")
    count = await session_mgmt.revoke_all_sessions(current_user.id)
    return RevokeSessionResponse(
        success=True,
        revoked_count=count,
        message=f"{count} session(s) revoked.",
    )
