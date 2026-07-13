"""
Unit tests for Phase 9.8 — AuthorizationService, AuthenticationMiddleware,
get_current_user DI, and the completed identity link/unlink endpoints.

All tests are isolated — zero real infrastructure.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.domain.models.auth import (
    AccountStatus, OAuthProvider, User, UserIdentity,
    UserRole, IdentityProvider,
)
from app.domain.models.request_context import (
    AuthenticatedPrincipal, CurrentSession, RequestContext,
)
from app.core.exceptions import (
    AuthenticationException, AccountNotActiveException, TokenExpiredException,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    user_id: str = "u-1",
    status: AccountStatus = AccountStatus.ACTIVE,
    verified: bool = True,
    identities: list | None = None,
) -> User:
    return User(
        id=user_id, email="user@example.com", username="testuser",
        display_name=None, avatar_url=None, role=UserRole.USER,
        status=status, created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc), verified=verified,
        identities=identities or [],
    )


def _make_principal(user_id: str = "u-1") -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        user_id=user_id, email="user@example.com", role=UserRole.USER
    )


# ============================================================================
# RequestContext domain model tests
# ============================================================================

class TestRequestContext:
    def test_anonymous_factory(self):
        ctx = RequestContext.anonymous(correlation_id="corr-1")
        assert ctx.is_authenticated is False
        assert ctx.principal is None
        assert ctx.user is None
        assert ctx.user_id is None
        assert ctx.correlation_id == "corr-1"
        assert ctx.is_admin is False
        assert ctx.is_active is False

    def test_authenticated_factory(self):
        principal = _make_principal()
        user = _make_user()
        ctx = RequestContext.authenticated(principal=principal, user=user, correlation_id="corr-2")
        assert ctx.is_authenticated is True
        assert ctx.user_id == "u-1"
        assert ctx.role == UserRole.USER
        assert ctx.is_active is True
        assert ctx.is_admin is False

    def test_is_active_false_when_suspended(self):
        user = _make_user(status=AccountStatus.SUSPENDED)
        principal = _make_principal()
        ctx = RequestContext.authenticated(principal=principal, user=user)
        assert ctx.is_active is False

    def test_is_active_false_when_unverified(self):
        user = _make_user(verified=False)
        ctx = RequestContext.authenticated(principal=_make_principal(), user=user)
        assert ctx.is_active is False

    def test_is_admin_true_for_admin_role(self):
        principal = AuthenticatedPrincipal(user_id="admin-1", email="a@b.com", role=UserRole.ADMIN)
        ctx = RequestContext.authenticated(principal=principal)
        assert ctx.is_admin is True


# ============================================================================
# AuthorizationService tests
# ============================================================================

class TestAuthorizationService:
    @pytest.fixture
    def token_service(self):
        return AsyncMock()

    @pytest.fixture
    def user_provider(self):
        return AsyncMock()

    @pytest.fixture
    def session_service(self):
        return AsyncMock()

    @pytest.fixture
    def authz(self, token_service, user_provider, session_service):
        from app.services.authorization import AuthorizationService
        return AuthorizationService(
            token_service=token_service,
            user_provider=user_provider,
            session_service=session_service,
        )

    @pytest.mark.asyncio
    async def test_valid_token_builds_context(self, authz, token_service, user_provider):
        user = _make_user()
        token_service.validate_token.return_value = {"sub": "u-1", "email": "user@example.com", "role": "user"}
        user_provider.get_by_id.return_value = user

        ctx = await authz.build_context("valid-token")

        assert ctx.is_authenticated is True
        assert ctx.user_id == "u-1"
        assert ctx.user.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_invalid_token_raises_authentication_exception(self, authz, token_service):
        token_service.validate_token.side_effect = AuthenticationException("Bad token.")

        with pytest.raises(AuthenticationException):
            await authz.build_context("bad-token")

    @pytest.mark.asyncio
    async def test_expired_token_raises_token_expired(self, authz, token_service):
        token_service.validate_token.side_effect = TokenExpiredException()

        with pytest.raises(TokenExpiredException):
            await authz.build_context("expired-token")

    @pytest.mark.asyncio
    async def test_suspended_account_raises(self, authz, token_service, user_provider):
        token_service.validate_token.return_value = {"sub": "u-1", "email": "x@x.com", "role": "user"}
        user_provider.get_by_id.return_value = _make_user(status=AccountStatus.SUSPENDED)

        with pytest.raises(AccountNotActiveException) as exc_info:
            await authz.build_context("valid-token")
        assert exc_info.value.error_code == "ACCOUNT_NOT_ACTIVE"

    @pytest.mark.asyncio
    async def test_unverified_account_raises(self, authz, token_service, user_provider):
        token_service.validate_token.return_value = {"sub": "u-1", "email": "x@x.com", "role": "user"}
        user_provider.get_by_id.return_value = _make_user(
            status=AccountStatus.PENDING_VERIFICATION, verified=False
        )

        with pytest.raises(AccountNotActiveException):
            await authz.build_context("valid-token")

    @pytest.mark.asyncio
    async def test_nonexistent_user_raises(self, authz, token_service, user_provider):
        token_service.validate_token.return_value = {"sub": "ghost", "email": "g@g.com", "role": "user"}
        user_provider.get_by_id.return_value = None

        with pytest.raises(AuthenticationException, match="no longer exists"):
            await authz.build_context("valid-token")

    @pytest.mark.asyncio
    async def test_missing_sub_claim_raises(self, authz, token_service):
        token_service.validate_token.return_value = {"email": "x@x.com"}  # no sub

        with pytest.raises(AuthenticationException, match="subject claim"):
            await authz.build_context("token-without-sub")

    @pytest.mark.asyncio
    async def test_admin_role_preserved(self, authz, token_service, user_provider):
        token_service.validate_token.return_value = {"sub": "admin-1", "email": "a@x.com", "role": "admin"}
        user_provider.get_by_id.return_value = _make_user(user_id="admin-1")

        ctx = await authz.build_context("admin-token")
        assert ctx.principal.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_anonymous_context(self, authz):
        ctx = await authz.build_anonymous_context(correlation_id="abc")
        assert ctx.is_authenticated is False
        assert ctx.correlation_id == "abc"

    @pytest.mark.asyncio
    async def test_session_built_from_claims(self, authz, token_service, user_provider, session_service):
        token_service.validate_token.return_value = {
            "sub": "u-1", "email": "u@x.com", "role": "user", "session_id": "sess-99"
        }
        user_provider.get_by_id.return_value = _make_user()
        session_service.validate_session.return_value = {"created_at": datetime.now(timezone.utc)}

        ctx = await authz.build_context("tok")
        assert ctx.session is not None
        assert ctx.session.session_id == "sess-99"

    @pytest.mark.asyncio
    async def test_expired_session_proceeds_with_token_auth(self, authz, token_service, user_provider, session_service):
        """Expired session should not block access — token auth still succeeds."""
        token_service.validate_token.return_value = {
            "sub": "u-1", "email": "u@x.com", "role": "user", "session_id": "old-sess"
        }
        user_provider.get_by_id.return_value = _make_user()
        session_service.validate_session.side_effect = Exception("Session expired")

        ctx = await authz.build_context("tok")
        # Still authenticated via token
        assert ctx.is_authenticated is True
        # Session is present but built from token fallback
        assert ctx.session is not None
        assert ctx.session.session_id == "old-sess"


# ============================================================================
# AuthenticationMiddleware tests
# ============================================================================

class TestAuthenticationMiddleware:
    def _make_request(self, auth_header: str | None = None) -> MagicMock:
        request = MagicMock()
        request.headers = {}
        if auth_header is not None:
            request.headers["Authorization"] = auth_header
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.state = MagicMock()
        request.state.auth_context = None
        return request

    @pytest.fixture
    def authz(self):
        return AsyncMock()

    @pytest.fixture
    def middleware(self, authz):
        from app.infrastructure.auth.middleware import AuthenticationMiddleware
        # We need to bypass BaseHTTPMiddleware's __init__ for unit testing
        mw = object.__new__(AuthenticationMiddleware)
        mw._authz = authz
        return mw

    def test_extract_bearer_valid(self, middleware):
        from app.infrastructure.auth.middleware import AuthenticationMiddleware
        req = self._make_request("Bearer my.valid.token123")
        token = AuthenticationMiddleware._extract_bearer(req)
        assert token == "my.valid.token123"

    def test_extract_bearer_none_when_missing(self, middleware):
        from app.infrastructure.auth.middleware import AuthenticationMiddleware
        req = self._make_request(None)
        assert AuthenticationMiddleware._extract_bearer(req) is None

    def test_extract_bearer_none_when_malformed(self, middleware):
        from app.infrastructure.auth.middleware import AuthenticationMiddleware
        req = self._make_request("Basic dXNlcjpwYXNz")
        assert AuthenticationMiddleware._extract_bearer(req) is None

    def test_extract_bearer_none_for_double_space(self, middleware):
        from app.infrastructure.auth.middleware import AuthenticationMiddleware
        req = self._make_request("Bearer  two-spaces")
        # Double space fails the regex
        assert AuthenticationMiddleware._extract_bearer(req) is None

    @pytest.mark.asyncio
    async def test_no_token_attaches_anonymous_context(self, middleware, authz):
        request = self._make_request(None)
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        ctx = request.state.auth_context
        assert ctx.is_authenticated is False
        authz.build_context.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_token_attaches_authenticated_context(self, middleware, authz):
        request = self._make_request("Bearer valid.token.here")
        principal = _make_principal()
        user = _make_user()
        authz.build_context.return_value = RequestContext.authenticated(principal=principal, user=user)
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        assert request.state.auth_context.is_authenticated is True

    @pytest.mark.asyncio
    async def test_expired_token_attaches_anonymous_with_error(self, middleware, authz):
        request = self._make_request("Bearer expired.token.here")
        authz.build_context.side_effect = TokenExpiredException()
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        assert request.state.auth_context.is_authenticated is False
        assert request.state.auth_error == "TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_inactive_account_attaches_anonymous_with_error(self, middleware, authz):
        request = self._make_request("Bearer suspended.token")
        authz.build_context.side_effect = AccountNotActiveException(status="suspended")
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        assert request.state.auth_context.is_authenticated is False
        assert request.state.auth_error == "ACCOUNT_NOT_ACTIVE"

    @pytest.mark.asyncio
    async def test_invalid_token_attaches_anonymous_with_error(self, middleware, authz):
        request = self._make_request("Bearer invalid.bad.token")
        authz.build_context.side_effect = AuthenticationException("Bad signature.")
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        assert request.state.auth_context.is_authenticated is False
        assert request.state.auth_error == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_always_calls_next(self, middleware, authz):
        """Middleware must always pass through — even on auth failure."""
        request = self._make_request("Bearer bad.token")
        authz.build_context.side_effect = AuthenticationException("Fail.")
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)

        call_next.assert_called_once()


# ============================================================================
# get_current_user DI tests (via HTTP test client)
# ============================================================================

class TestGetCurrentUserDI:
    @pytest.fixture(scope="class")
    def app(self):
        from app.main import app as fastapi_app
        return fastapi_app

    @pytest.fixture
    def user(self):
        return _make_user()

    def test_authenticated_request_returns_user(self, app, user):
        from fastapi.testclient import TestClient
        from app.dependencies.services import get_current_user, get_authentication_api_service
        from app.api.v1.auth.dtos import AccessValidationResponse

        mock_auth_api = AsyncMock()
        mock_auth_api.validate_access.return_value = AccessValidationResponse(
            success=True, user=MagicMock(
                user_id="u-1", email="u@e.com", username="u", display_name=None,
                avatar_url=None, role="user", status="active", verified=True, identities=[]
            ),
            token_claims={"sub": "u-1"},
        )

        # Override get_current_user to return a domain User directly
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_authentication_api_service] = lambda: mock_auth_api

        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/api/v1/auth/me", headers={"Authorization": "Bearer tok"})

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["user"]["user_id"] == "u-1"

    def test_unauthenticated_request_returns_401(self, app):
        from fastapi.testclient import TestClient
        from app.dependencies.services import get_current_user

        def _raise_401():
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "AUTHENTICATION_ERROR", "message": "Authentication required."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        app.dependency_overrides[get_current_user] = _raise_401

        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/api/v1/auth/me")

        app.dependency_overrides.clear()
        assert resp.status_code == 401
        assert "WWW-Authenticate" in resp.headers


# ============================================================================
# Identity link/unlink endpoint tests (now working implementations)
# ============================================================================

class TestIdentityEndpoints:
    @pytest.fixture(scope="class")
    def app(self):
        from app.main import app as fastapi_app
        return fastapi_app

    def _setup(self, app, user, link_result=None, unlink_result=None):
        from app.dependencies.services import get_current_user, get_authentication_api_service
        from app.api.v1.auth.dtos import ApiError, IdentityLinkResponse as ILR

        mock_auth_api = AsyncMock()
        if link_result is not None:
            mock_auth_api.link_identity.return_value = link_result
        if unlink_result is not None:
            mock_auth_api.unlink_identity.return_value = unlink_result

        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_authentication_api_service] = lambda: mock_auth_api
        return mock_auth_api

    @pytest.fixture
    def user(self):
        return _make_user(identities=[
            UserIdentity(
                id="id-1", user_id="u-1", provider=IdentityProvider.OAUTH,
                oauth_provider=OAuthProvider.GOOGLE, provider_id="g-sub-1",
                created_at=datetime.now(timezone.utc),
            )
        ])

    def test_link_identity_success(self, app, user):
        from fastapi.testclient import TestClient
        from app.api.v1.auth.dtos import IdentityLinkResponse as ILR, AuthenticatedUserResponse
        from app.api.v1.auth.dtos import IdentityResponse

        linked_user = AuthenticatedUserResponse(
            user_id="u-1", email="u@e.com", username="u",
            display_name=None, avatar_url=None, role="user",
            status="active", verified=True, identities=[
                IdentityResponse(provider="oauth", oauth_provider="github",
                                 provider_id="gh-1", linked_at=datetime.now(timezone.utc))
            ]
        )
        self._setup(app, user, link_result=ILR(success=True, user=linked_user))

        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/api/v1/auth/identity/link", json={
                "provider": "github", "code": "auth-code", "redirect_uri": "https://app.example.com/cb"
            }, headers={"Authorization": "Bearer tok"})

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_link_identity_already_linked_409(self, app, user):
        from fastapi.testclient import TestClient
        from app.api.v1.auth.dtos import IdentityLinkResponse as ILR, ApiError

        self._setup(app, user, link_result=ILR(
            success=False, error=ApiError(code="CONFLICT", message="Already linked.")
        ))

        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/api/v1/auth/identity/link", json={
                "provider": "github", "code": "code", "redirect_uri": "https://x.com/cb"
            }, headers={"Authorization": "Bearer tok"})

        app.dependency_overrides.clear()
        assert resp.status_code == 409

    def test_unlink_identity_success(self, app, user):
        from fastapi.testclient import TestClient
        from app.api.v1.auth.dtos import IdentityLinkResponse as ILR, AuthenticatedUserResponse

        updated_user = AuthenticatedUserResponse(
            user_id="u-1", email="u@e.com", username="u",
            display_name=None, avatar_url=None, role="user",
            status="active", verified=True, identities=[]
        )
        self._setup(app, user, unlink_result=ILR(success=True, user=updated_user))

        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.delete(
                "/api/v1/auth/identity/google",
                headers={"Authorization": "Bearer tok"},
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_unlink_last_identity_400(self, app, user):
        from fastapi.testclient import TestClient
        from app.api.v1.auth.dtos import IdentityLinkResponse as ILR, ApiError

        self._setup(app, user, unlink_result=ILR(
            success=False, error=ApiError(code="VALIDATION_ERROR", message="Last identity.")
        ))

        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.delete(
                "/api/v1/auth/identity/google",
                headers={"Authorization": "Bearer tok"},
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 400

    def test_unknown_provider_400(self, app, user):
        from fastapi.testclient import TestClient
        from app.dependencies.services import get_current_user, get_authentication_api_service

        mock_api = AsyncMock()
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_authentication_api_service] = lambda: mock_api

        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.delete(
                "/api/v1/auth/identity/fakeapp",
                headers={"Authorization": "Bearer tok"},
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 400
