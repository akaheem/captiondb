"""
Request Context domain models.

These are pure, immutable dataclasses with zero framework coupling.
They represent the authenticated identity attached to every request.

No FastAPI. No Pydantic. No JWT. No infrastructure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from app.domain.models.auth import OAuthProvider, User, UserRole, AccountStatus


# ---------------------------------------------------------------------------
# AuthenticatedPrincipal
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """
    The verified identity extracted from a validated access token.

    This is the minimal set of claims we can trust from the token alone
    — before any database round-trip.  It is populated by the middleware
    from the validated token payload and stored on the request for cheap
    repeated access.
    """
    user_id: str
    email: str
    role: UserRole
    token_jti: Optional[str] = None           # JWT ID for replay tracking (future)
    token_issued_at: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None
    oauth_provider: Optional[OAuthProvider] = None
    claims: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# CurrentSession
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CurrentSession:
    """
    Representation of the active server-side session associated with
    the current request.

    Populated only when the request carries a session_id in the token
    claims or a matching session record exists in the session store.
    """
    session_id: str
    user_id: str
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# RequestContext
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RequestContext:
    """
    The authoritative source of authentication information for a single
    HTTP request.

    Lifecycle:
      1. AuthenticationMiddleware validates the Bearer token.
      2. AuthorizationService builds a RequestContext from the token claims
         and optionally hydrates the full User.
      3. The context is stored in request.state.auth_context.
      4. get_request_context() and get_current_user() DI functions read it.

    Anonymous requests have is_authenticated = False and all optional
    fields set to None.
    """
    is_authenticated: bool
    principal: Optional[AuthenticatedPrincipal] = None
    user: Optional[User] = None
    session: Optional[CurrentSession] = None
    correlation_id: Optional[str] = None

    @property
    def user_id(self) -> Optional[str]:
        return self.principal.user_id if self.principal else None

    @property
    def role(self) -> Optional[UserRole]:
        return self.principal.role if self.principal else None

    @property
    def is_admin(self) -> bool:
        return self.principal is not None and self.principal.role == UserRole.ADMIN

    @property
    def is_active(self) -> bool:
        """True only when the user record is loaded and the account is active."""
        return (
            self.user is not None
            and self.user.status == AccountStatus.ACTIVE
            and self.user.verified
        )

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def anonymous(cls, correlation_id: Optional[str] = None) -> "RequestContext":
        """Create a context representing an unauthenticated request."""
        return cls(is_authenticated=False, correlation_id=correlation_id)

    @classmethod
    def authenticated(
        cls,
        principal: AuthenticatedPrincipal,
        user: Optional[User] = None,
        session: Optional[CurrentSession] = None,
        correlation_id: Optional[str] = None,
    ) -> "RequestContext":
        """Create a context representing a successfully authenticated request."""
        return cls(
            is_authenticated=True,
            principal=principal,
            user=user,
            session=session,
            correlation_id=correlation_id,
        )
