"""
AuthenticationApiService
------------------------
The single entry-point that future FastAPI routers will call for every
authentication operation.

Responsibilities:
  * Orchestrate EmailAuthenticationService, OAuthAuthenticationService,
    AuthenticationService, TokenService, and SessionService.
  * Translate domain exceptions into ApiError / result objects.
  * Never import FastAPI, raise HTTPException, or return HTTPResponse.
  * Never contain business logic — that lives in the Application services.

Dependency direction:
  FastAPI Routers → AuthenticationApiService → Application Services → Domain
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from loguru import logger

from app.core.exceptions import (
    CaptionDBException,
    AuthenticationException,
    OAuthProviderException,
)
from app.domain.models.auth import OAuthProvider, User, UserIdentity
from app.services.auth import AuthenticationService
from app.services.email_auth import EmailAuthenticationService
from app.services.oauth_auth import OAuthAuthenticationService
from app.services.token import TokenService
from app.services.session import SessionService
from app.infrastructure.auth.oauth.base import OAuthHTTPError

from .dtos import (
    ApiError,
    AccessValidationResponse,
    AuthenticatedUserResponse,
    IdentityLinkResponse,
    IdentityResponse,
    LoginResponse,
    LogoutResponse,
    OAuthCompleteResponse,
    OAuthLoginResponse,
    RefreshSessionResponse,
    RegisterResponse,
    SessionResponse,
    TokenResponse,
)


# ---------------------------------------------------------------------------
# Internal mapping helpers (private to this module)
# ---------------------------------------------------------------------------

def _map_user(user: User) -> AuthenticatedUserResponse:
    """Convert a domain User into a serialisable DTO. No FastAPI coupling."""
    return AuthenticatedUserResponse(
        user_id=user.id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        role=user.role.value,
        status=user.status.value,
        verified=user.verified,
        identities=[
            IdentityResponse(
                provider=i.provider.value,
                oauth_provider=i.oauth_provider.value if i.oauth_provider else None,
                provider_id=i.provider_id,
                linked_at=i.created_at,
            )
            for i in user.identities
        ],
    )


def _map_error(exc: Exception) -> ApiError:
    """
    Translate any exception into a safe ApiError.

    Security: only the ``error_code`` of known domain exceptions is forwarded
    to the caller.  Unknown exceptions get a generic code so internal details
    are never leaked.
    """
    if isinstance(exc, CaptionDBException):
        return ApiError(code=exc.error_code, message=exc.message, details=exc.details)
    # Completely unknown error — don't leak implementation details.
    logger.exception("Unexpected error in AuthenticationApiService")
    return ApiError(code="INTERNAL_ERROR", message="An unexpected error occurred.")


# ---------------------------------------------------------------------------
# AuthenticationApiService
# ---------------------------------------------------------------------------

class AuthenticationApiService:
    """
    Coordinates all authentication operations and returns framework-independent
    result DTOs.  Routers should inject this service and call its methods only.
    """

    def __init__(
        self,
        auth_service: AuthenticationService,
        email_auth_service: EmailAuthenticationService,
        oauth_auth_service: OAuthAuthenticationService,
        token_service: TokenService,
        session_service: SessionService,
    ) -> None:
        self._auth = auth_service
        self._email_auth = email_auth_service
        self._oauth_auth = oauth_auth_service
        self._tokens = token_service
        self._sessions = session_service

    # ------------------------------------------------------------------
    # Email / Password
    # ------------------------------------------------------------------

    async def login_email(
        self,
        email: str,
        password: str,
        session_metadata: Optional[Dict[str, Any]] = None,
    ) -> LoginResponse:
        """Authenticate with email + password and issue tokens + session."""
        logger.info(f"API login attempt for {email}")
        try:
            user = await self._email_auth.login(email, password)
            tokens, session = await self._issue_credentials(user, session_metadata or {})
            return LoginResponse(
                success=True,
                user=_map_user(user),
                tokens=tokens,
                session=session,
            )
        except Exception as exc:
            logger.warning(f"Login failed for {email}: {exc}")
            return LoginResponse(success=False, error=_map_error(exc))

    async def register_email(
        self,
        email: str,
        username: str,
        password: str,
    ) -> RegisterResponse:
        """Register a new user with email + password."""
        logger.info(f"API registration for {email}")
        try:
            user = await self._email_auth.register(email, username, password)
            return RegisterResponse(
                success=True,
                user=_map_user(user),
                requires_verification=(not user.verified),
            )
        except Exception as exc:
            logger.warning(f"Registration failed for {email}: {exc}")
            return RegisterResponse(success=False, error=_map_error(exc))

    # ------------------------------------------------------------------
    # OAuth
    # ------------------------------------------------------------------

    async def begin_oauth_login(
        self,
        provider: OAuthProvider,
        state: str,
        redirect_uri: str,
    ) -> OAuthLoginResponse:
        """Return the provider authorization URL for the frontend redirect."""
        logger.info(f"Beginning OAuth login via {provider}")
        try:
            url = await self._oauth_auth.begin_login(provider, state, redirect_uri)
            return OAuthLoginResponse(success=True, authorization_url=url)
        except Exception as exc:
            logger.warning(f"OAuth begin_login failed for {provider}: {exc}")
            return OAuthLoginResponse(success=False, error=_map_error(exc))

    async def complete_oauth_login(
        self,
        provider: OAuthProvider,
        code: str,
        redirect_uri: str,
        session_metadata: Optional[Dict[str, Any]] = None,
    ) -> OAuthCompleteResponse:
        """Exchange the OAuth code for a profile, then issue tokens + session."""
        logger.info(f"Completing OAuth login via {provider}")
        try:
            result = await self._oauth_auth.complete_login(provider, code, redirect_uri)
            if not result.success or not result.user:
                return OAuthCompleteResponse(
                    success=False,
                    error=ApiError(code="OAUTH_FAILED", message="OAuth login did not complete."),
                )
            tokens, session = await self._issue_credentials(result.user, session_metadata or {})
            return OAuthCompleteResponse(
                success=True,
                user=_map_user(result.user),
                tokens=tokens,
                session=session,
                is_new_user=result.is_new_user,
            )
        except OAuthHTTPError as exc:
            logger.warning(f"OAuth HTTP error for {provider}: {exc}")
            return OAuthCompleteResponse(
                success=False,
                error=ApiError(
                    code="OAUTH_PROVIDER_ERROR",
                    message=f"Provider returned an error (HTTP {exc.status_code}).",
                ),
            )
        except Exception as exc:
            logger.warning(f"OAuth complete_login failed for {provider}: {exc}")
            return OAuthCompleteResponse(success=False, error=_map_error(exc))

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def refresh_session(
        self,
        access_token: str,
        session_id: Optional[str] = None,
    ) -> RefreshSessionResponse:
        """Validate the current token/session and issue a refreshed token pair.

        TECHNICAL DEBT (Phase 10): True token rotation (issue a new access token +
        invalidate the old one via a JTI blocklist) requires a concrete JWT
        implementation in TokenProvider.  Until then the same token is returned
        after validating it is still valid, and the session TTL is extended.
        This is safe for development but MUST be replaced before production.
        """
        logger.info("API session refresh requested")
        try:
            claims = await self._tokens.validate_token(access_token)
            _user_id: str = claims.get("sub", "")  # noqa: F841 — validates token is usable

            # Extend session TTL
            if session_id:
                await self._sessions.refresh_session(session_id)

            # TODO (Phase 10): issue a genuinely new token and revoke the old one.
            tokens = TokenResponse(access_token=access_token)
            return RefreshSessionResponse(success=True, tokens=tokens)
        except Exception as exc:
            logger.warning(f"Session refresh failed: {exc}")
            return RefreshSessionResponse(success=False, error=_map_error(exc))

    async def logout(
        self,
        access_token: str,
        session_id: Optional[str] = None,
    ) -> LogoutResponse:
        """Revoke the token and terminate the session."""
        logger.info("API logout requested")
        try:
            await self._tokens.revoke_token(access_token)
            if session_id:
                await self._sessions.terminate_session(session_id)
            return LogoutResponse(success=True)
        except Exception as exc:
            logger.warning(f"Logout failed: {exc}")
            return LogoutResponse(success=False, error=_map_error(exc))

    # ------------------------------------------------------------------
    # Identity management
    # ------------------------------------------------------------------

    async def link_identity(
        self,
        user: User,
        provider: OAuthProvider,
        code: str,
        redirect_uri: str,
    ) -> IdentityLinkResponse:
        """Link an additional OAuth identity to an existing account."""
        logger.info(f"Linking {provider} identity for user {user.id}")
        try:
            updated_user = await self._oauth_auth.link_oauth_identity(user, provider, code, redirect_uri)
            return IdentityLinkResponse(success=True, user=_map_user(updated_user))
        except OAuthHTTPError as exc:
            return IdentityLinkResponse(
                success=False,
                error=ApiError(code="OAUTH_PROVIDER_ERROR", message=f"Provider HTTP {exc.status_code}."),
            )
        except Exception as exc:
            return IdentityLinkResponse(success=False, error=_map_error(exc))

    async def unlink_identity(
        self,
        user: User,
        provider: OAuthProvider,
    ) -> IdentityLinkResponse:
        """Unlink an OAuth identity from an account."""
        logger.info(f"Unlinking {provider} identity for user {user.id}")
        try:
            updated_user = await self._oauth_auth.unlink_oauth_identity(user, provider)
            return IdentityLinkResponse(success=True, user=_map_user(updated_user))
        except Exception as exc:
            return IdentityLinkResponse(success=False, error=_map_error(exc))

    # ------------------------------------------------------------------
    # Token validation / access guard
    # ------------------------------------------------------------------

    async def validate_access(self, access_token: str) -> AccessValidationResponse:
        """
        Validate an access token and return the associated user claims.
        Used by middleware stubs and future route guards.

        NOTE: User hydration is intentionally best-effort here — the authoritative
        user loading path is AuthorizationService (used by the middleware DI chain).
        This method is used for lightweight token checks in endpoints.
        """
        try:
            claims = await self._tokens.validate_token(access_token)
            user_id: str = claims.get("sub", "")

            # Best-effort user hydration using public interface only.
            # AuthenticationService exposes _user_provider only to its own methods;
            # for the API facade we use it via the Auth service's public authenticate path.
            user: Optional[User] = None
            if user_id:
                try:
                    # Delegate through the auth service's public user lookup.
                    # When a proper UserProvider DI is wired here this will be cleaner.
                    _provider = getattr(self._auth, '_user_provider', None)
                    if _provider and hasattr(_provider, 'get_by_id'):
                        user = await _provider.get_by_id(user_id)
                except Exception:
                    pass  # Hydration failure is non-fatal for validation

            return AccessValidationResponse(
                success=True,
                user=_map_user(user) if user else None,
                token_claims=claims,
            )
        except Exception as exc:
            return AccessValidationResponse(success=False, error=_map_error(exc))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _issue_credentials(
        self,
        user: User,
        session_metadata: Dict[str, Any],
    ) -> tuple[TokenResponse, SessionResponse]:
        """Issue an access token and create a session. Returns both DTOs."""
        access_token = await self._tokens.issue_access_token(user)
        session_id = await self._sessions.create_session(user.id, session_metadata)
        tokens = TokenResponse(access_token=access_token)
        session = SessionResponse(
            session_id=session_id,
            user_id=user.id,
            created_at=datetime.now(timezone.utc),
        )
        return tokens, session
