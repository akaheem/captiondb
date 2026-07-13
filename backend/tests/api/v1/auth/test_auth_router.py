"""
API integration tests for /api/v1/auth endpoints (Phase 9.7).

All tests use FastAPI's TestClient with AuthenticationApiService overridden
via dependency_overrides — zero infrastructure, zero real tokens.

Coverage:
  POST /register      success / conflict / weak password
  POST /login         success / bad credentials / inactive account
  POST /logout        success / missing token
  POST /refresh       success / expired token
  GET  /me            success / no token / invalid token
  POST /oauth/{p}/begin    success / unknown provider
  GET  /oauth/{p}/callback success new user / provider error
  GET  /validate      valid / invalid
  Error mapping       all ApiError codes → correct HTTP status
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth.dtos import (
    AccessValidationResponse,
    ApiError,
    AuthenticatedUserResponse,
    IdentityLinkResponse as IdentityLinkDTO,
    LoginResponse as LoginDTO,
    LogoutResponse as LogoutDTO,
    OAuthCompleteResponse,
    OAuthLoginResponse,
    RefreshSessionResponse,
    RegisterResponse as RegisterDTO,
    SessionResponse,
    TokenResponse,
)
from app.dependencies.services import get_authentication_api_service

# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def mock_auth_api():
    return AsyncMock()


@pytest.fixture
def client(app, mock_auth_api):
    app.dependency_overrides[get_authentication_api_service] = lambda: mock_auth_api
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c, mock_auth_api
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_dto(user_id: str = "u-1", verified: bool = True) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(
        user_id=user_id, email="user@example.com", username="testuser",
        display_name=None, avatar_url=None, role="user",
        status="active", verified=verified, identities=[],
    )


def _token_dto() -> TokenResponse:
    return TokenResponse(access_token="acc-tok", token_type="Bearer", expires_in=3600)


def _session_dto() -> SessionResponse:
    return SessionResponse(session_id="sess-1", user_id="u-1", created_at=datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_success_201(self, client):
        c, api = client
        api.register_email.return_value = RegisterDTO(
            success=True, user=_user_dto(verified=False), requires_verification=True
        )
        resp = c.post("/api/v1/auth/register", json={
            "email": "new@example.com", "username": "newuser", "password": "Str0ng!Pass"
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["requires_verification"] is True

    def test_conflict_409(self, client):
        c, api = client
        api.register_email.return_value = RegisterDTO(
            success=False, error=ApiError(code="CONFLICT", message="Email already in use.")
        )
        resp = c.post("/api/v1/auth/register", json={
            "email": "dupe@example.com", "username": "u", "password": "Str0ng!Pass"
        })
        assert resp.status_code == 409

    def test_weak_password_400(self, client):
        c, api = client
        api.register_email.return_value = RegisterDTO(
            success=False, error=ApiError(code="VALIDATION_ERROR", message="Weak password.")
        )
        resp = c.post("/api/v1/auth/register", json={
            "email": "u@e.com", "username": "user", "password": "Str0ng!Pass"
        })
        assert resp.status_code == 400

    def test_pydantic_validation_422(self, client):
        c, api = client
        resp = c.post("/api/v1/auth/register", json={"email": "not-an-email", "username": "u", "password": "p"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_success_200(self, client):
        c, api = client
        api.login_email.return_value = LoginDTO(
            success=True, user=_user_dto(), tokens=_token_dto(), session=_session_dto()
        )
        resp = c.post("/api/v1/auth/login", json={"email": "u@e.com", "password": "pass"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["tokens"]["access_token"] == "acc-tok"
        assert body["session"]["session_id"] == "sess-1"

    def test_bad_credentials_401(self, client):
        c, api = client
        api.login_email.return_value = LoginDTO(
            success=False, error=ApiError(code="INVALID_CREDENTIALS", message="Bad creds.")
        )
        resp = c.post("/api/v1/auth/login", json={"email": "u@e.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_account_not_active_403(self, client):
        c, api = client
        api.login_email.return_value = LoginDTO(
            success=False, error=ApiError(code="ACCOUNT_NOT_ACTIVE", message="Suspended.")
        )
        resp = c.post("/api/v1/auth/login", json={"email": "u@e.com", "password": "pw"})
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_success_200(self, client):
        c, api = client
        api.logout.return_value = LogoutDTO(success=True)
        resp = c.post(
            "/api/v1/auth/logout",
            json={"session_id": "sess-1"},
            headers={"Authorization": "Bearer valid-tok"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_missing_token_401(self, client):
        c, api = client
        resp = c.post("/api/v1/auth/logout", json={})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------

class TestRefresh:
    def test_success_200(self, client):
        c, api = client
        api.refresh_session.return_value = RefreshSessionResponse(
            success=True, tokens=_token_dto()
        )
        resp = c.post(
            "/api/v1/auth/refresh", json={},
            headers={"Authorization": "Bearer valid-tok"},
        )
        assert resp.status_code == 200
        assert resp.json()["tokens"]["access_token"] == "acc-tok"

    def test_expired_token_401(self, client):
        c, api = client
        api.refresh_session.return_value = RefreshSessionResponse(
            success=False, error=ApiError(code="TOKEN_EXPIRED", message="Expired.")
        )
        resp = c.post(
            "/api/v1/auth/refresh", json={},
            headers={"Authorization": "Bearer old-tok"},
        )
        assert resp.status_code == 401

    def test_missing_token_401(self, client):
        c, api = client
        resp = c.post("/api/v1/auth/refresh", json={})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

class TestMe:
    def test_success_200(self, client):
        c, api = client
        api.validate_access.return_value = AccessValidationResponse(
            success=True, user=_user_dto(), token_claims={"sub": "u-1"}
        )
        resp = c.get("/api/v1/auth/me", headers={"Authorization": "Bearer tok"})
        assert resp.status_code == 200
        assert resp.json()["user"]["user_id"] == "u-1"

    def test_no_token_401(self, client):
        c, api = client
        resp = c.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_invalid_token_401(self, client):
        c, api = client
        api.validate_access.return_value = AccessValidationResponse(
            success=False, error=ApiError(code="AUTHENTICATION_ERROR", message="Bad token.")
        )
        resp = c.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /oauth/{provider}/begin
# ---------------------------------------------------------------------------

class TestOAuthBegin:
    def test_success_200(self, client):
        c, api = client
        api.begin_oauth_login.return_value = OAuthLoginResponse(
            success=True, authorization_url="https://accounts.google.com/auth?..."
        )
        resp = c.post("/api/v1/auth/oauth/google/begin", json={
            "state": "random-opaque-state-string",
            "redirect_uri": "https://app.example.com/cb",
        })
        assert resp.status_code == 200
        assert "authorization_url" in resp.json()

    def test_unknown_provider_400(self, client):
        c, api = client
        resp = c.post("/api/v1/auth/oauth/fakeapp/begin", json={
            "state": "state12345678", "redirect_uri": "https://x.com/cb"
        })
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /oauth/{provider}/callback
# ---------------------------------------------------------------------------

class TestOAuthCallback:
    def test_success_new_user_200(self, client):
        c, api = client
        api.complete_oauth_login.return_value = OAuthCompleteResponse(
            success=True, user=_user_dto(), tokens=_token_dto(),
            session=_session_dto(), is_new_user=True,
        )
        resp = c.get(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "auth-code", "state": "opaque-state", "redirect_uri": "https://app.example.com/cb"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_new_user"] is True

    def test_provider_error_502(self, client):
        c, api = client
        api.complete_oauth_login.return_value = OAuthCompleteResponse(
            success=False, error=ApiError(code="OAUTH_PROVIDER_ERROR", message="Bad gateway.")
        )
        resp = c.get(
            "/api/v1/auth/oauth/github/callback",
            params={"code": "bad", "state": "s", "redirect_uri": "https://x.com/cb"},
        )
        assert resp.status_code == 502

    def test_unknown_provider_400(self, client):
        c, api = client
        resp = c.get(
            "/api/v1/auth/oauth/fakeapp/callback",
            params={"code": "c", "state": "s", "redirect_uri": "https://x.com/cb"},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /validate
# ---------------------------------------------------------------------------

class TestValidate:
    def test_valid_token_200(self, client):
        c, api = client
        api.validate_access.return_value = AccessValidationResponse(
            success=True, user=_user_dto(), token_claims={"sub": "u-1", "role": "user"}
        )
        resp = c.get("/api/v1/auth/validate", headers={"Authorization": "Bearer valid"})
        assert resp.status_code == 200
        assert resp.json()["token_claims"]["sub"] == "u-1"

    def test_expired_token_401(self, client):
        c, api = client
        api.validate_access.return_value = AccessValidationResponse(
            success=False, error=ApiError(code="TOKEN_EXPIRED", message="Expired.")
        )
        resp = c.get("/api/v1/auth/validate", headers={"Authorization": "Bearer old"})
        assert resp.status_code == 401

    def test_missing_token_401(self, client):
        c, api = client
        resp = c.get("/api/v1/auth/validate")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Error mapping table
# ---------------------------------------------------------------------------

class TestErrorMapping:
    @pytest.mark.parametrize("code,expected_status", [
        ("INVALID_CREDENTIALS",    401),
        ("AUTHENTICATION_ERROR",   401),
        ("ACCOUNT_NOT_ACTIVE",     403),
        ("TOKEN_EXPIRED",          401),
        ("NOT_FOUND",              404),
        ("CONFLICT",               409),
        ("IDENTITY_ALREADY_LINKED",409),
        ("IDENTITY_NOT_FOUND",     404),
        ("VALIDATION_ERROR",       400),
        ("OAUTH_PROVIDER_ERROR",   502),
        ("OAUTH_FAILED",           400),
        ("INTERNAL_ERROR",         500),
    ])
    def test_error_code_to_http_status(self, code: str, expected_status: int, client):
        """Verify that every ApiError code maps to the correct HTTP status."""
        from app.api.v1.auth.router import _ERROR_STATUS_MAP
        assert _ERROR_STATUS_MAP.get(code) == expected_status
