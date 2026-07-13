"""
SessionManagementService — Application service.

Responsibilities:
  • list_sessions()            — return all active sessions for a user
  • get_session()              — fetch a single session by ID
  • refresh_session()          — extend a session's TTL
  • revoke_session()           — terminate one session (validates ownership)
  • revoke_all_sessions()      — terminate every session for a user
  • cleanup_expired_sessions() — purge expired sessions (background-safe)

Constraints:
  NO FastAPI imports.
  NO JWT parsing.
  Pure orchestration — delegates all I/O to SessionProvider.

Architecture:
  Routers → AuthenticationApiService → SessionManagementService → SessionProvider → Infrastructure
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.exceptions import (
    CaptionDBException,
    NotFoundException,
    AuthenticationException,
)
from app.domain.interfaces.auth import SessionProvider


# ---------------------------------------------------------------------------
# Session domain DTO (no DB schema — maps to whatever SessionProvider returns)
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class SessionInfo:
    """
    Read model for a user session.  Built from raw session-store data.
    Never used as a persistence model — that belongs to the infrastructure layer.
    """
    session_id: str
    user_id: str
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_expired: bool = False
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)


def _parse_session(session_id: str, raw: Dict[str, Any]) -> SessionInfo:
    """Convert raw session-store dict to a typed SessionInfo."""

    def _dt(key: str) -> Optional[datetime]:
        val = raw.get(key)
        if val is None:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(str(val))
        except (ValueError, TypeError):
            return None

    return SessionInfo(
        session_id=session_id,
        user_id=raw.get("user_id", ""),
        created_at=_dt("created_at") or datetime.now(timezone.utc),
        last_seen_at=_dt("last_seen_at"),
        ip_address=raw.get("ip_address"),
        user_agent=raw.get("user_agent"),
        is_expired=bool(raw.get("is_expired", False)),
        metadata={k: v for k, v in raw.items()
                  if k not in {"user_id", "created_at", "last_seen_at",
                               "ip_address", "user_agent", "is_expired"}},
    )


class SessionManagementService:
    """
    Manages the full session lifecycle for a user.
    All operations are user-scoped — cross-user access is prevented.
    """

    def __init__(self, session_provider: SessionProvider) -> None:
        self._provider = session_provider

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def list_sessions(self, user_id: str) -> List[SessionInfo]:
        """Return all known sessions for a user, newest first."""
        logger.info(f"Listing sessions for user {user_id}")
        try:
            # SessionProvider.list_sessions is a forward-compatible extension.
            if hasattr(self._provider, "list_sessions"):
                raws: List[Dict[str, Any]] = await self._provider.list_sessions(user_id)
            else:
                # Fallback: provider has no list capability — return empty.
                logger.warning("SessionProvider does not implement list_sessions.")
                return []
            return [_parse_session(r.get("session_id", ""), r) for r in raws]
        except Exception as exc:
            logger.error(f"Failed to list sessions for user {user_id}: {exc}")
            raise CaptionDBException(
                "Failed to list sessions.", error_code="SESSION_LIST_ERROR"
            ) from exc

    async def get_session(self, session_id: str, user_id: str) -> SessionInfo:
        """
        Fetch one session by ID.  Validates ownership — raises NotFoundException
        when the session does not belong to user_id.
        """
        raw = await self._provider.get_session(session_id)
        if raw is None:
            raise NotFoundException(f"Session '{session_id}' not found.")

        info = _parse_session(session_id, raw)
        if info.user_id and info.user_id != user_id:
            # Ownership mismatch — treat as not-found (no information leak)
            raise NotFoundException(f"Session '{session_id}' not found.")
        return info

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def refresh_session(self, session_id: str, user_id: str) -> SessionInfo:
        """Extend the session TTL.  Validates ownership before refresh."""
        logger.info(f"Refreshing session {session_id} for user {user_id}")
        # Validate ownership
        await self.get_session(session_id, user_id)

        if hasattr(self._provider, "refresh_session"):
            await self._provider.refresh_session(session_id)
        else:
            logger.warning("SessionProvider does not implement refresh_session — no-op.")

        raw = await self._provider.get_session(session_id)
        if raw is None:
            raise NotFoundException(f"Session '{session_id}' disappeared after refresh.")
        return _parse_session(session_id, raw)

    async def revoke_session(self, session_id: str, user_id: str) -> None:
        """
        Terminate a single session.  Validates ownership.
        Silently succeeds if the session is already gone (idempotent).
        """
        logger.info(f"Revoking session {session_id} for user {user_id}")
        raw = await self._provider.get_session(session_id)
        if raw is None:
            # Already gone — idempotent success
            return

        info = _parse_session(session_id, raw)
        if info.user_id and info.user_id != user_id:
            raise NotFoundException(f"Session '{session_id}' not found.")

        await self._provider.revoke_session(session_id)

    async def revoke_all_sessions(self, user_id: str) -> int:
        """
        Revoke every active session for a user.

        Returns the number of sessions revoked.
        Uses SessionProvider.revoke_all_sessions() if available, otherwise
        falls back to listing + revoking one by one.
        """
        logger.info(f"Revoking all sessions for user {user_id}")
        if hasattr(self._provider, "revoke_all_sessions"):
            count: int = await self._provider.revoke_all_sessions(user_id)
            return count

        # Fallback — fetch list and revoke individually
        sessions = await self.list_sessions(user_id)
        for s in sessions:
            try:
                await self._provider.revoke_session(s.session_id)
            except Exception as exc:
                logger.warning(f"Failed to revoke session {s.session_id}: {exc}")
        return len(sessions)

    async def cleanup_expired_sessions(self, user_id: str) -> int:
        """
        Remove sessions flagged as expired.

        Returns the number cleaned up.
        Background-task-safe — errors are logged, never raised.
        """
        logger.info(f"Cleaning up expired sessions for user {user_id}")
        try:
            if hasattr(self._provider, "cleanup_expired_sessions"):
                return await self._provider.cleanup_expired_sessions(user_id)

            sessions = await self.list_sessions(user_id)
            expired = [s for s in sessions if s.is_expired]
            for s in expired:
                try:
                    await self._provider.revoke_session(s.session_id)
                except Exception:
                    pass
            return len(expired)
        except Exception as exc:
            logger.error(f"cleanup_expired_sessions failed for user {user_id}: {exc}")
            return 0
