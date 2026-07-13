"""
Unit tests for AuthenticationApiService (Phase 9.6).

Every application service dependency is mocked so these tests run with no
infrastructure (no DB, no Redis, no HTTP, no JWT).

Coverage:
  - login_email      (success / bad credentials)
  - register_email   (success / conflict / weak password)
  - begin_oauth_login (success / unknown provider)
  - complete_oauth_login (success new user / success existing user / provider error)
  - refresh_session  (success / invalid token)
  - logout           (success / revocation error)
  - link_identity    (success / already linked)
  - unlink_identity  (success / last identity)
  - validate_access  (valid token / expired token)
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.v1.auth.service import AuthenticationApiService
from app.api.v1.auth.dtos import (
    LoginResponse,
    RegisterResponse,
    OAuthLoginResponse,
    OAuthCompleteResponse,
    RefreshSessionResponse,
    LogoutResponse,
    IdentityLinkResponse,
    AccessValidationResponse,
)
from app.domain.models.auth import (
    User, UserIdentity, OAuthProvider, AccountStatus, UserRole, IdentityProvider
)
from app.domain.models.oauth import OAuthAuthenticationResult, OAuthTokenBundle
from app.core.exceptions import CaptionDBException
from app.infrastructure.auth.oauth.base import OAuthHTTPError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    user_id: str = "user-1",
    email: str = "user@example.com",
    verified: bool = True,
    status: AccountStatus = AccountStatus.ACTIVE,
    identities: list | None = None,
) -> User:
    return User(
        id=user_id,
        email=email,
        username="testuser",
        display_name="Test User",
        avatar_url=None,
        role=UserRole.USER,
        status=status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        verified=verified,
        identities=identities or [],
    )


def _make_identity(provider: OAuthProvider = OAuthProvider.GOOGLE) -> UserIdentity:
    return UserIdentity(
        id="id-1",
        user_id="user-1",
        provider=IdentityProvider.OAUTH,
        oauth_provider=provider,
        provider_id="prov-sub-123",
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_service():
    svc = MagicMock()
    svc._user_provider = AsyncMock()
    return svc


@pytest.fixture
def email_auth_service():
    return AsyncMock()


@pytest.fixture
def oauth_auth_service():
    return AsyncMock()


@pytest.fixture
def token_service():
    return AsyncMock()


@pytest.fixture
def session_service():
    return AsyncMock()


@pytest.fixture
def api_service(auth_service, email_auth_service, oauth_auth_service, token_service, session_service):
    return AuthenticationApiService(
        auth_service=auth_service,
        email_auth_service=email_auth_service,
        oauth_auth_service=oauth_auth_service,
        token_service=token_service,
        session_service=session_service,
    )


# ---------------------------------------------------------------------------
# login_email
# ---------------------------------------------------------------------------

class TestLoginEmail:
    @pytest.mark.asyncio
    async def test_success(self, api_service, email_auth_service, token_service, session_service):
        user = _make_user()
        email_auth_service.login.return_value = user
        token_service.issue_access_token.return_value = "access-tok"
        session_service.create_session.return_value = "sess-id"

        result = await api_service.login_email("user@example.com", "Password1!")

        assert isinstance(result, LoginResponse)
        assert result.success is True
        assert result.error is None
        assert result.user is not None
        assert result.user.user_id == "user-1"
        assert result.tokens is not None
        assert result.tokens.access_token == "access-tok"
        assert result.session is not None
        assert result.session.session_id == "sess-id"

    @pytest.mark.asyncio
    async def test_bad_credentials(self, api_service, email_auth_service):
        email_auth_service.login.side_effect = CaptionDBException(
            "Invalid credentials.", error_code="AUTHENTICATION_ERROR"
        )

        result = await api_service.login_email("user@example.com", "wrong")

        assert result.success is False
        assert result.user is None
        assert result.tokens is None
        assert result.error is not None
        assert result.error.code == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_unknown_exception_returns_generic_error(self, api_service, email_auth_service):
        email_auth_service.login.side_effect = RuntimeError("something exploded")

        result = await api_service.login_email("user@example.com", "pw")

        assert result.success is False
        assert result.error.code == "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# register_email
# ---------------------------------------------------------------------------

class TestRegisterEmail:
    @pytest.mark.asyncio
    async def test_success(self, api_service, email_auth_service):
        user = _make_user(verified=False, status=AccountStatus.PENDING_VERIFICATION)
        email_auth_service.register.return_value = user

        result = await api_service.register_email("new@example.com", "newuser", "Str0ng!Pass")

        assert isinstance(result, RegisterResponse)
        assert result.success is True
        assert result.requires_verification is True
        assert result.user.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_duplicate_email(self, api_service, email_auth_service):
        email_auth_service.register.side_effect = CaptionDBException(
            "Email is already in use.", error_code="CONFLICT"
        )

        result = await api_service.register_email("dupe@example.com", "u", "pass")

        assert result.success is False
        assert result.error.code == "CONFLICT"

    @pytest.mark.asyncio
    async def test_weak_password(self, api_service, email_auth_service):
        email_auth_service.register.side_effect = CaptionDBException(
            "Password does not meet strength requirements.", error_code="VALIDATION_ERROR"
        )

        result = await api_service.register_email("u@e.com", "u", "weak")

        assert result.success is False
        assert result.error.code == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# begin_oauth_login
# ---------------------------------------------------------------------------

class TestBeginOAuthLogin:
    @pytest.mark.asyncio
    async def test_success(self, api_service, oauth_auth_service):
        oauth_auth_service.begin_login.return_value = "https://accounts.google.com/o/oauth2/v2/auth?..."

        result = await api_service.begin_oauth_login(
            OAuthProvider.GOOGLE, "state123", "http://localhost/callback"
        )

        assert isinstance(result, OAuthLoginResponse)
        assert result.success is True
        assert result.authorization_url is not None
        assert "google" in result.authorization_url or "accounts" in result.authorization_url

    @pytest.mark.asyncio
    async def test_unknown_provider(self, api_service, oauth_auth_service):
        oauth_auth_service.begin_login.side_effect = CaptionDBException(
            "Provider GITHUB is not registered.", error_code="INTERNAL_ERROR"
        )

        result = await api_service.begin_oauth_login(
            OAuthProvider.GITHUB, "state", "http://localhost/cb"
        )

        assert result.success is False
        assert result.authorization_url is None
        assert result.error.code == "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# complete_oauth_login
# ---------------------------------------------------------------------------

class TestCompleteOAuthLogin:
    @pytest.mark.asyncio
    async def test_success_existing_user(self, api_service, oauth_auth_service, token_service, session_service):
        user = _make_user(identities=[_make_identity()])
        oauth_auth_service.complete_login.return_value = OAuthAuthenticationResult(
            success=True, user=user, tokens=OAuthTokenBundle(access_token="oauth-acc"), is_new_user=False
        )
        token_service.issue_access_token.return_value = "issued-tok"
        session_service.create_session.return_value = "sess-99"

        result = await api_service.complete_oauth_login(
            OAuthProvider.GOOGLE, "code123", "http://localhost/cb"
        )

        assert isinstance(result, OAuthCompleteResponse)
        assert result.success is True
        assert result.is_new_user is False
        assert result.user.user_id == "user-1"
        assert result.tokens.access_token == "issued-tok"

    @pytest.mark.asyncio
    async def test_success_new_user(self, api_service, oauth_auth_service, token_service, session_service):
        user = _make_user()
        oauth_auth_service.complete_login.return_value = OAuthAuthenticationResult(
            success=True, user=user, tokens=OAuthTokenBundle(access_token="tok"), is_new_user=True
        )
        token_service.issue_access_token.return_value = "tok"
        session_service.create_session.return_value = "sess"

        result = await api_service.complete_oauth_login(
            OAuthProvider.GITHUB, "code", "http://localhost/cb"
        )

        assert result.success is True
        assert result.is_new_user is True

    @pytest.mark.asyncio
    async def test_provider_http_error(self, api_service, oauth_auth_service):
        oauth_auth_service.complete_login.side_effect = OAuthHTTPError(400, "invalid_grant")

        result = await api_service.complete_oauth_login(
            OAuthProvider.GOOGLE, "bad-code", "http://localhost/cb"
        )

        assert result.success is False
        assert result.error.code == "OAUTH_PROVIDER_ERROR"

    @pytest.mark.asyncio
    async def test_returns_failure_when_result_not_successful(self, api_service, oauth_auth_service):
        oauth_auth_service.complete_login.return_value = OAuthAuthenticationResult(
            success=False, user=None
        )

        result = await api_service.complete_oauth_login(
            OAuthProvider.GOOGLE, "code", "http://localhost/cb"
        )

        assert result.success is False
        assert result.error.code == "OAUTH_FAILED"


# ---------------------------------------------------------------------------
# refresh_session
# ---------------------------------------------------------------------------

class TestRefreshSession:
    @pytest.mark.asyncio
    async def test_success(self, api_service, token_service, session_service):
        token_service.validate_token.return_value = {"sub": "user-1"}
        session_service.refresh_session.return_value = None

        result = await api_service.refresh_session("valid-token", session_id="sess-1")

        assert isinstance(result, RefreshSessionResponse)
        assert result.success is True
        assert result.tokens is not None
        session_service.refresh_session.assert_called_once_with("sess-1")

    @pytest.mark.asyncio
    async def test_invalid_token(self, api_service, token_service):
        token_service.validate_token.side_effect = CaptionDBException(
            "Invalid or expired token.", error_code="AUTHENTICATION_ERROR"
        )

        result = await api_service.refresh_session("expired-token")

        assert result.success is False
        assert result.error.code == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_no_session_id_skips_session_refresh(self, api_service, token_service, session_service):
        token_service.validate_token.return_value = {"sub": "user-1"}

        result = await api_service.refresh_session("tok")

        assert result.success is True
        session_service.refresh_session.assert_not_called()


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

class TestLogout:
    @pytest.mark.asyncio
    async def test_success(self, api_service, token_service, session_service):
        token_service.revoke_token.return_value = None
        session_service.terminate_session.return_value = None

        result = await api_service.logout("tok", session_id="sess-1")

        assert isinstance(result, LogoutResponse)
        assert result.success is True
        token_service.revoke_token.assert_called_once_with("tok")
        session_service.terminate_session.assert_called_once_with("sess-1")

    @pytest.mark.asyncio
    async def test_revocation_failure(self, api_service, token_service):
        token_service.revoke_token.side_effect = NotImplementedError("not wired")

        result = await api_service.logout("tok")

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_no_session_skips_session_termination(self, api_service, token_service, session_service):
        token_service.revoke_token.return_value = None

        result = await api_service.logout("tok")

        assert result.success is True
        session_service.terminate_session.assert_not_called()


# ---------------------------------------------------------------------------
# link_identity / unlink_identity
# ---------------------------------------------------------------------------

class TestIdentityLinking:
    @pytest.mark.asyncio
    async def test_link_success(self, api_service, oauth_auth_service):
        user = _make_user()
        updated_user = _make_user(identities=[_make_identity()])
        oauth_auth_service.link_oauth_identity.return_value = updated_user

        result = await api_service.link_identity(
            user, OAuthProvider.GOOGLE, "code", "http://localhost/cb"
        )

        assert isinstance(result, IdentityLinkResponse)
        assert result.success is True
        assert len(result.user.identities) == 1

    @pytest.mark.asyncio
    async def test_link_already_linked(self, api_service, oauth_auth_service):
        oauth_auth_service.link_oauth_identity.side_effect = CaptionDBException(
            "Identity type is already linked.", error_code="CONFLICT"
        )

        result = await api_service.link_identity(
            _make_user(), OAuthProvider.GOOGLE, "code", "http://localhost/cb"
        )

        assert result.success is False
        assert result.error.code == "CONFLICT"

    @pytest.mark.asyncio
    async def test_link_oauth_http_error(self, api_service, oauth_auth_service):
        oauth_auth_service.link_oauth_identity.side_effect = OAuthHTTPError(401, "Unauthorized")

        result = await api_service.link_identity(
            _make_user(), OAuthProvider.GITHUB, "bad-code", "http://localhost/cb"
        )

        assert result.success is False
        assert result.error.code == "OAUTH_PROVIDER_ERROR"

    @pytest.mark.asyncio
    async def test_unlink_success(self, api_service, oauth_auth_service):
        user = _make_user(identities=[_make_identity()])
        updated_user = _make_user(identities=[])
        oauth_auth_service.unlink_oauth_identity.return_value = updated_user

        result = await api_service.unlink_identity(user, OAuthProvider.GOOGLE)

        assert result.success is True
        assert len(result.user.identities) == 0

    @pytest.mark.asyncio
    async def test_unlink_last_identity_raises(self, api_service, oauth_auth_service):
        oauth_auth_service.unlink_oauth_identity.side_effect = CaptionDBException(
            "Cannot unlink the last remaining identity.", error_code="VALIDATION_ERROR"
        )

        result = await api_service.unlink_identity(_make_user(), OAuthProvider.GOOGLE)

        assert result.success is False
        assert result.error.code == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# validate_access
# ---------------------------------------------------------------------------

class TestValidateAccess:
    @pytest.mark.asyncio
    async def test_valid_token(self, api_service, token_service):
        token_service.validate_token.return_value = {"sub": "user-1", "role": "user"}

        result = await api_service.validate_access("valid-tok")

        assert isinstance(result, AccessValidationResponse)
        assert result.success is True
        assert result.token_claims == {"sub": "user-1", "role": "user"}

    @pytest.mark.asyncio
    async def test_expired_token(self, api_service, token_service):
        token_service.validate_token.side_effect = CaptionDBException(
            "Token has expired.", error_code="TOKEN_EXPIRED"
        )

        result = await api_service.validate_access("expired-tok")

        assert result.success is False
        assert result.error.code == "TOKEN_EXPIRED"
        assert result.token_claims is None
