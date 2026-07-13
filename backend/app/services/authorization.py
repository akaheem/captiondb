"""
AuthorizationService — Application service.

Responsibilities:
  • Parse and validate an access token (via TokenService)
  • Load the authenticated User (via UserProvider)
  • Validate account status
  • Validate session (via SessionService, if session_id is in claims)
  • Build and return an immutable RequestContext

Constraints:
  NO FastAPI imports.
  NO JWT library imports — token parsing is fully delegated to TokenService.
  NO HTTP response types.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from loguru import logger

from app.core.exceptions import (
    AuthenticationException,
    AccountNotActiveException,
    TokenExpiredException,
)
from app.domain.models.auth import AccountStatus, OAuthProvider, UserRole
from app.domain.models.request_context import (
    AuthenticatedPrincipal,
    CurrentSession,
    RequestContext,
)
from app.domain.interfaces.auth import UserProvider
from app.services.token import TokenService
from app.services.session import SessionService


class AuthorizationService:
    """
    Orchestrates token validation, user hydration and session verification
    to produce a RequestContext for every authenticated request.

    This is a pure Application service — no infrastructure, no HTTP.
    """

    def __init__(
        self,
        token_service: TokenService,
        user_provider: UserProvider,
        session_service: SessionService,
    ) -> None:
        self._tokens = token_service
        self._users = user_provider
        self._sessions = session_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def build_context(
        self,
        bearer_token: str,
        correlation_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> RequestContext:
        """
        Validate the bearer token, hydrate the user, validate the session,
        and return an authenticated RequestContext.

        Raises:
            AuthenticationException  — token is malformed or signature fails.
            TokenExpiredException    — token exists but has expired.
            AccountNotActiveException — user account is suspended/unverified.
        """
        # 1. Validate token — raises on failure
        claims = await self._validate_token(bearer_token)

        # 2. Build principal from claims (cheap — no DB call)
        principal = self._build_principal(claims)

        # 3. Hydrate User from provider (single DB call per request)
        user = await self._load_user(principal.user_id)

        # 4. Validate account status
        self._validate_account(user.status, user.verified)

        # 5. Validate session if session_id is in the claims (best-effort)
        session = await self._build_session(
            claims, user.id, ip_address, user_agent
        )

        logger.debug(
            f"AuthorizationService: authenticated user_id={user.id} "
            f"role={principal.role.value} corr_id={correlation_id}"
        )

        return RequestContext.authenticated(
            principal=principal,
            user=user,
            session=session,
            correlation_id=correlation_id,
        )

    async def build_anonymous_context(
        self, correlation_id: Optional[str] = None
    ) -> RequestContext:
        """Return an anonymous (unauthenticated) context — no validation."""
        return RequestContext.anonymous(correlation_id=correlation_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _validate_token(self, token: str) -> Dict[str, Any]:
        """Delegate entirely to TokenService — no JWT parsing here."""
        try:
            return await self._tokens.validate_token(token)
        except TokenExpiredException:
            raise
        except Exception as exc:
            raise AuthenticationException(f"Token validation failed: {exc}") from exc

    def _build_principal(self, claims: Dict[str, Any]) -> AuthenticatedPrincipal:
        """Extract a typed AuthenticatedPrincipal from raw token claims."""
        user_id = claims.get("sub") or claims.get("user_id", "")
        if not user_id:
            raise AuthenticationException("Token is missing subject claim.")

        raw_role = claims.get("role", UserRole.USER.value)
        try:
            role = UserRole(raw_role)
        except ValueError:
            role = UserRole.USER

        raw_provider = claims.get("oauth_provider")
        oauth_provider: Optional[OAuthProvider] = None
        if raw_provider:
            try:
                oauth_provider = OAuthProvider(raw_provider)
            except ValueError:
                pass

        issued_at: Optional[datetime] = None
        expires_at: Optional[datetime] = None
        if "iat" in claims:
            try:
                issued_at = datetime.fromtimestamp(claims["iat"], tz=timezone.utc)
            except (TypeError, ValueError):
                pass
        if "exp" in claims:
            try:
                expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
            except (TypeError, ValueError):
                pass

        return AuthenticatedPrincipal(
            user_id=user_id,
            email=claims.get("email", ""),
            role=role,
            token_jti=claims.get("jti"),
            token_issued_at=issued_at,
            token_expires_at=expires_at,
            oauth_provider=oauth_provider,
            claims=claims,
        )

    async def _load_user(self, user_id: str):
        """Fetch the full User from the UserProvider."""
        try:
            user = await self._users.get_by_id(user_id)
        except Exception as exc:
            raise AuthenticationException(f"Could not load user: {exc}") from exc

        if user is None:
            raise AuthenticationException("Authenticated user no longer exists.")
        return user

    def _validate_account(self, status: AccountStatus, verified: bool) -> None:
        """Ensure the account is in a state that permits access."""
        if status == AccountStatus.SUSPENDED:
            raise AccountNotActiveException(
                status=status.value,
                details={"reason": "Account has been suspended."},
            )
        if status == AccountStatus.PENDING_VERIFICATION or not verified:
            raise AccountNotActiveException(
                status=status.value,
                details={"reason": "Account email is not yet verified."},
            )
        if status != AccountStatus.ACTIVE:
            raise AccountNotActiveException(status=status.value)

    async def _build_session(
        self,
        claims: Dict[str, Any],
        user_id: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> Optional[CurrentSession]:
        """
        Build a CurrentSession from claims.

        If the token carries a session_id we verify it is still alive;
        if not, we still return a lightweight session from the token data.
        """
        session_id: Optional[str] = claims.get("session_id") or claims.get("sid")
        if not session_id:
            return None

        try:
            session_data = await self._sessions.validate_session(session_id)
            return CurrentSession(
                session_id=session_id,
                user_id=user_id,
                created_at=session_data.get("created_at", datetime.now(timezone.utc)),
                last_seen_at=datetime.now(timezone.utc),
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=session_data,
            )
        except Exception:
            # Session is missing or expired — still allow access if token is valid.
            # Strict session validation can be enforced per-endpoint via DI.
            logger.warning(
                f"Session {session_id} could not be validated — "
                "proceeding with token-only authentication."
            )
            return CurrentSession(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                ip_address=ip_address,
                user_agent=user_agent,
            )
