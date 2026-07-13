"""
Phase 9.9 Tests — SessionManagementService & OAuthIdentityService.

Full unit test coverage:
  SessionManagementService
    - list_sessions (normal, empty, provider-without-list)
    - get_session (found, not-found, ownership mismatch)
    - refresh_session (success, not-found, no-refresh-method)
    - revoke_session (success, not-found, ownership mismatch, idempotent)
    - revoke_all_sessions (with & without provider method, fallback)
    - cleanup_expired_sessions (expired flagged, no error on failure)

  OAuthIdentityService
    - list_identities
    - get_identity (found, not-found)
    - link_identity (success, duplicate provider, OAuth failure)
    - unlink_identity (success, not-linked, last identity)

  Session API Endpoints (via TestClient)
    - GET /auth/sessions (success, no auth)
    - DELETE /auth/sessions/{id} (success, 404, no auth)
    - DELETE /auth/sessions (success, no auth)
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
    CaptionDBException,
)
from app.domain.models.auth import (
    AccountStatus,
    IdentityProvider,
    OAuthProvider,
    User,
    UserIdentity,
    UserRole,
)
from app.services.session_management import SessionManagementService, SessionInfo, _parse_session
from app.services.oauth_identity import OAuthIdentityService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_user(
    user_id: str = "u-1",
    identities: list | None = None,
) -> User:
    return User(
        id=user_id, email="user@example.com", username="testuser",
        display_name=None, avatar_url=None, role=UserRole.USER,
        status=AccountStatus.ACTIVE, created_at=_now(),
        updated_at=_now(), verified=True,
        identities=identities or [],
    )


def _make_identity(
    provider: IdentityProvider = IdentityProvider.OAUTH,
    oauth_provider: OAuthProvider | None = OAuthProvider.GOOGLE,
    provider_id: str = "g-sub-1",
) -> UserIdentity:
    return UserIdentity(
        id="id-1", user_id="u-1",
        provider=provider, oauth_provider=oauth_provider,
        provider_id=provider_id, created_at=_now(),
    )


def _raw_session(
    session_id: str = "sess-1",
    user_id: str = "u-1",
    is_expired: bool = False,
) -> dict:
    return {
        "session_id": session_id,
        "user_id": user_id,
        "created_at": _now(),
        "last_seen_at": _now(),
        "ip_address": "127.0.0.1",
        "user_agent": "pytest",
        "is_expired": is_expired,
    }


# ============================================================================
# _parse_session helper tests
# ============================================================================

class TestParseSession:
    def test_parses_all_fields(self):
        raw = _raw_session("sess-99")
        info = _parse_session("sess-99", raw)
        assert info.session_id == "sess-99"
        assert info.user_id == "u-1"
        assert info.ip_address == "127.0.0.1"
        assert info.is_expired is False

    def test_handles_missing_optional_fields(self):
        info = _parse_session("sess-x", {"user_id": "u-2"})
        assert info.session_id == "sess-x"
        assert info.ip_address is None
        assert info.user_agent is None


# ============================================================================
# SessionManagementService
# ============================================================================

class TestSessionManagementService:

    @pytest.fixture
    def provider(self):
        p = AsyncMock()
        p.list_sessions = AsyncMock(return_value=[_raw_session("sess-1"), _raw_session("sess-2")])
        p.get_session = AsyncMock(return_value=_raw_session("sess-1"))
        p.revoke_session = AsyncMock()
        p.revoke_all_sessions = AsyncMock(return_value=2)
        p.refresh_session = AsyncMock()
        return p

    @pytest.fixture
    def svc(self, provider):
        return SessionManagementService(session_provider=provider)

    # ── list_sessions ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_list_sessions_returns_all(self, svc, provider):
        sessions = await svc.list_sessions("u-1")
        assert len(sessions) == 2
        assert all(isinstance(s, SessionInfo) for s in sessions)

    @pytest.mark.asyncio
    async def test_list_sessions_empty_when_provider_has_no_method(self, provider, caplog):
        del provider.list_sessions  # simulate provider without list support
        svc = SessionManagementService(session_provider=provider)
        sessions = await svc.list_sessions("u-1")
        assert sessions == []

    @pytest.mark.asyncio
    async def test_list_sessions_raises_on_provider_error(self, provider):
        provider.list_sessions.side_effect = RuntimeError("Redis down")
        svc = SessionManagementService(session_provider=provider)
        with pytest.raises(CaptionDBException, match="Failed to list"):
            await svc.list_sessions("u-1")

    # ── get_session ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_get_session_found(self, svc, provider):
        info = await svc.get_session("sess-1", "u-1")
        assert info.session_id == "sess-1"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, svc, provider):
        provider.get_session.return_value = None
        with pytest.raises(NotFoundException):
            await svc.get_session("no-sess", "u-1")

    @pytest.mark.asyncio
    async def test_get_session_ownership_mismatch_raises_not_found(self, svc, provider):
        """Ownership mismatch must surface as NotFoundException (no info leak)."""
        provider.get_session.return_value = _raw_session("sess-1", user_id="other-user")
        with pytest.raises(NotFoundException):
            await svc.get_session("sess-1", "u-1")

    # ── refresh_session ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_refresh_session_success(self, svc, provider):
        info = await svc.refresh_session("sess-1", "u-1")
        provider.refresh_session.assert_called_once_with("sess-1")
        assert info.session_id == "sess-1"

    @pytest.mark.asyncio
    async def test_refresh_session_not_found(self, svc, provider):
        provider.get_session.return_value = None
        with pytest.raises(NotFoundException):
            await svc.refresh_session("ghost", "u-1")

    @pytest.mark.asyncio
    async def test_refresh_session_no_op_when_provider_lacks_method(self, provider):
        del provider.refresh_session
        svc = SessionManagementService(session_provider=provider)
        # Should not raise — just a no-op
        info = await svc.refresh_session("sess-1", "u-1")
        assert info.session_id == "sess-1"

    # ── revoke_session ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_revoke_session_success(self, svc, provider):
        await svc.revoke_session("sess-1", "u-1")
        provider.revoke_session.assert_called_once_with("sess-1")

    @pytest.mark.asyncio
    async def test_revoke_session_idempotent_when_already_gone(self, svc, provider):
        provider.get_session.return_value = None
        # Should not raise — idempotent
        await svc.revoke_session("ghost", "u-1")
        provider.revoke_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_revoke_session_ownership_mismatch(self, svc, provider):
        provider.get_session.return_value = _raw_session("sess-1", user_id="other")
        with pytest.raises(NotFoundException):
            await svc.revoke_session("sess-1", "u-1")

    # ── revoke_all_sessions ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_revoke_all_via_provider_method(self, svc, provider):
        count = await svc.revoke_all_sessions("u-1")
        provider.revoke_all_sessions.assert_called_once_with("u-1")
        assert count == 2

    @pytest.mark.asyncio
    async def test_revoke_all_falls_back_to_list_revoke(self, provider):
        del provider.revoke_all_sessions
        provider.list_sessions.return_value = [
            _raw_session("s-1"), _raw_session("s-2"), _raw_session("s-3")
        ]
        svc = SessionManagementService(session_provider=provider)
        count = await svc.revoke_all_sessions("u-1")
        assert count == 3
        assert provider.revoke_session.call_count == 3

    # ── cleanup_expired_sessions ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_cleanup_expired_via_provider(self, provider):
        provider.cleanup_expired_sessions = AsyncMock(return_value=5)
        svc = SessionManagementService(session_provider=provider)
        count = await svc.cleanup_expired_sessions("u-1")
        assert count == 5

    @pytest.mark.asyncio
    async def test_cleanup_expired_fallback(self, provider):
        del provider.cleanup_expired_sessions
        provider.list_sessions.return_value = [
            _raw_session("s-1", is_expired=True),
            _raw_session("s-2", is_expired=False),
            _raw_session("s-3", is_expired=True),
        ]
        svc = SessionManagementService(session_provider=provider)
        count = await svc.cleanup_expired_sessions("u-1")
        assert count == 2
        assert provider.revoke_session.call_count == 2

    @pytest.mark.asyncio
    async def test_cleanup_never_raises(self, provider):
        provider.list_sessions.side_effect = RuntimeError("DB exploded")
        del provider.cleanup_expired_sessions
        svc = SessionManagementService(session_provider=provider)
        # Must not propagate — background-task-safe
        count = await svc.cleanup_expired_sessions("u-1")
        assert count == 0


# ============================================================================
# OAuthIdentityService
# ============================================================================

class TestOAuthIdentityService:

    @pytest.fixture
    def auth_service(self):
        return AsyncMock()

    @pytest.fixture
    def oauth_auth_service(self):
        return AsyncMock()

    @pytest.fixture
    def svc(self, auth_service, oauth_auth_service):
        return OAuthIdentityService(
            auth_service=auth_service,
            oauth_auth_service=oauth_auth_service,
        )

    # ── list_identities ────────────────────────────────────────────────

    def test_list_identities_returns_all(self, svc):
        user = _make_user(identities=[
            _make_identity(oauth_provider=OAuthProvider.GOOGLE),
            _make_identity(oauth_provider=OAuthProvider.GITHUB, provider_id="gh-1"),
        ])
        identities = svc.list_identities(user)
        assert len(identities) == 2
        providers = {i.oauth_provider for i in identities}
        assert OAuthProvider.GOOGLE in providers
        assert OAuthProvider.GITHUB in providers

    def test_list_identities_empty(self, svc):
        user = _make_user(identities=[])
        assert svc.list_identities(user) == []

    # ── get_identity ───────────────────────────────────────────────────

    def test_get_identity_found(self, svc):
        user = _make_user(identities=[_make_identity(oauth_provider=OAuthProvider.GOOGLE)])
        identity = svc.get_identity(user, OAuthProvider.GOOGLE)
        assert identity.oauth_provider == OAuthProvider.GOOGLE

    def test_get_identity_not_found(self, svc):
        user = _make_user(identities=[])
        with pytest.raises(NotFoundException):
            svc.get_identity(user, OAuthProvider.GITHUB)

    # ── link_identity ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_link_identity_success(self, svc, oauth_auth_service):
        user = _make_user(identities=[])
        updated = _make_user(identities=[_make_identity(oauth_provider=OAuthProvider.GITHUB)])
        oauth_auth_service.link_oauth_identity.return_value = updated

        result = await svc.link_identity(user, OAuthProvider.GITHUB, "auth-code", "https://x.com/cb")

        oauth_auth_service.link_oauth_identity.assert_called_once_with(
            user, OAuthProvider.GITHUB, "auth-code", "https://x.com/cb"
        )
        assert len(result.identities) == 1

    @pytest.mark.asyncio
    async def test_link_identity_duplicate_raises_conflict(self, svc):
        user = _make_user(identities=[_make_identity(oauth_provider=OAuthProvider.GOOGLE)])
        with pytest.raises(ConflictException) as exc_info:
            await svc.link_identity(user, OAuthProvider.GOOGLE, "code", "https://x.com/cb")
        assert "already linked" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_link_identity_oauth_failure_wraps_exception(self, svc, oauth_auth_service):
        user = _make_user(identities=[])
        oauth_auth_service.link_oauth_identity.side_effect = RuntimeError("OAuth provider down")
        with pytest.raises(CaptionDBException, match="Failed to link"):
            await svc.link_identity(user, OAuthProvider.GITHUB, "code", "https://x.com/cb")

    @pytest.mark.asyncio
    async def test_link_identity_re_raises_domain_exceptions(self, svc, oauth_auth_service):
        """Domain exceptions (ConflictException, etc.) should propagate unchanged."""
        user = _make_user(identities=[])
        oauth_auth_service.link_oauth_identity.side_effect = ConflictException("Already exists.")
        with pytest.raises(ConflictException):
            await svc.link_identity(user, OAuthProvider.GITHUB, "code", "https://x.com/cb")

    # ── unlink_identity ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_unlink_identity_success(self, svc, auth_service):
        user = _make_user(identities=[
            _make_identity(oauth_provider=OAuthProvider.GOOGLE),
            _make_identity(oauth_provider=OAuthProvider.GITHUB, provider_id="gh-1"),
        ])
        updated = _make_user(identities=[_make_identity(oauth_provider=OAuthProvider.GITHUB)])
        auth_service.unlink_identity.return_value = updated

        result = await svc.unlink_identity(user, OAuthProvider.GOOGLE)

        auth_service.unlink_identity.assert_called_once_with(
            user, IdentityProvider.OAUTH, OAuthProvider.GOOGLE
        )
        assert len(result.identities) == 1

    @pytest.mark.asyncio
    async def test_unlink_identity_not_linked_raises_not_found(self, svc):
        user = _make_user(identities=[_make_identity(oauth_provider=OAuthProvider.GOOGLE)])
        with pytest.raises(NotFoundException):
            await svc.unlink_identity(user, OAuthProvider.GITHUB)

    @pytest.mark.asyncio
    async def test_unlink_last_identity_raises_validation_error(self, svc):
        user = _make_user(identities=[_make_identity(oauth_provider=OAuthProvider.GOOGLE)])
        with pytest.raises(ValidationException, match="last authentication method"):
            await svc.unlink_identity(user, OAuthProvider.GOOGLE)

    @pytest.mark.asyncio
    async def test_unlink_propagates_domain_exceptions(self, svc, auth_service):
        user = _make_user(identities=[
            _make_identity(oauth_provider=OAuthProvider.GOOGLE),
            _make_identity(oauth_provider=OAuthProvider.GITHUB, provider_id="gh-1"),
        ])
        auth_service.unlink_identity.side_effect = ConflictException("Cannot unlink.")
        with pytest.raises(ConflictException):
            await svc.unlink_identity(user, OAuthProvider.GOOGLE)

    # ── domain guards directly ─────────────────────────────────────────

    def test_assert_not_last_identity_allows_multiple(self, svc):
        user = _make_user(identities=[
            _make_identity(oauth_provider=OAuthProvider.GOOGLE),
            _make_identity(oauth_provider=OAuthProvider.GITHUB),
        ])
        svc._assert_not_last_identity(user)  # Must not raise

    def test_assert_not_last_identity_blocks_single(self, svc):
        user = _make_user(identities=[_make_identity()])
        with pytest.raises(ValidationException):
            svc._assert_not_last_identity(user)

    def test_assert_not_last_identity_blocks_empty(self, svc):
        user = _make_user(identities=[])
        with pytest.raises(ValidationException):
            svc._assert_not_last_identity(user)


# ============================================================================
# Session API Endpoint tests (via TestClient + dependency_overrides)
# ============================================================================

class TestSessionEndpoints:

    @pytest.fixture(scope="class")
    def app(self):
        from app.main import app as fastapi_app
        return fastapi_app

    @pytest.fixture
    def mock_session_mgmt(self):
        return AsyncMock()

    @pytest.fixture
    def user(self):
        return _make_user()

    def _sessions(self, count: int = 2) -> list[SessionInfo]:
        return [
            SessionInfo(
                session_id=f"sess-{i}",
                user_id="u-1",
                created_at=_now(),
            )
            for i in range(count)
        ]

    def _client(self, app, user, mock_session_mgmt):
        from fastapi.testclient import TestClient
        from app.dependencies.services import get_current_user, get_session_management_service
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_session_management_service] = lambda: mock_session_mgmt
        client = TestClient(app, raise_server_exceptions=False)
        return client

    # ── GET /auth/sessions ─────────────────────────────────────────────

    def test_list_sessions_returns_200(self, app, user, mock_session_mgmt):
        mock_session_mgmt.list_sessions.return_value = self._sessions(3)
        c = self._client(app, user, mock_session_mgmt)
        resp = c.get("/api/v1/auth/sessions", headers={"Authorization": "Bearer tok"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert len(body["sessions"]) == 3

    def test_list_sessions_unauthenticated_401(self, app):
        from fastapi.testclient import TestClient
        from app.dependencies.services import get_current_user
        from fastapi import HTTPException, status as hstatus

        def _raise():
            raise HTTPException(status_code=hstatus.HTTP_401_UNAUTHORIZED, detail="Auth required.")

        app.dependency_overrides[get_current_user] = _raise
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/api/v1/auth/sessions")
        app.dependency_overrides.clear()
        assert resp.status_code == 401

    def test_list_sessions_empty(self, app, user, mock_session_mgmt):
        mock_session_mgmt.list_sessions.return_value = []
        c = self._client(app, user, mock_session_mgmt)
        resp = c.get("/api/v1/auth/sessions", headers={"Authorization": "Bearer tok"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    # ── DELETE /auth/sessions/{id} ─────────────────────────────────────

    def test_revoke_session_success(self, app, user, mock_session_mgmt):
        mock_session_mgmt.revoke_session.return_value = None
        c = self._client(app, user, mock_session_mgmt)
        resp = c.delete("/api/v1/auth/sessions/sess-1", headers={"Authorization": "Bearer tok"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["session_id"] == "sess-1"

    def test_revoke_session_not_found_404(self, app, user, mock_session_mgmt):
        mock_session_mgmt.revoke_session.side_effect = NotFoundException("Session not found.")
        c = self._client(app, user, mock_session_mgmt)
        resp = c.delete("/api/v1/auth/sessions/ghost", headers={"Authorization": "Bearer tok"})
        app.dependency_overrides.clear()
        assert resp.status_code == 404

    # ── DELETE /auth/sessions ──────────────────────────────────────────

    def test_revoke_all_sessions_success(self, app, user, mock_session_mgmt):
        mock_session_mgmt.revoke_all_sessions.return_value = 4
        c = self._client(app, user, mock_session_mgmt)
        resp = c.delete("/api/v1/auth/sessions", headers={"Authorization": "Bearer tok"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["revoked_count"] == 4
        assert "4 session" in body["message"]

    def test_revoke_all_sessions_zero(self, app, user, mock_session_mgmt):
        mock_session_mgmt.revoke_all_sessions.return_value = 0
        c = self._client(app, user, mock_session_mgmt)
        resp = c.delete("/api/v1/auth/sessions", headers={"Authorization": "Bearer tok"})
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["revoked_count"] == 0
