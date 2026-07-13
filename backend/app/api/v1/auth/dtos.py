"""
Authentication API DTOs.

Pure Python dataclasses that form the contract between the
AuthenticationApiService and whatever HTTP layer eventually sits above it.

Rules:
- No FastAPI imports.
- No Pydantic (yet — the HTTP layer will wrap these in schemas).
- No domain model references — this is the translation boundary.
- All fields use JSON-serialisable primitives only.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ApiError:
    """Standardised error envelope returned on any failure path."""
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ApiResult:
    """
    Generic result wrapper.  The HTTP layer inspects ``success`` to decide
    the status code; it never raises exceptions up to the router.
    """
    success: bool
    error: Optional[ApiError] = None


# ---------------------------------------------------------------------------
# Token & Session primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TokenResponse:
    """Issued access + refresh tokens."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None


@dataclass(frozen=True)
class SessionResponse:
    """Thin representation of an active session."""
    session_id: str
    user_id: str
    created_at: datetime


# ---------------------------------------------------------------------------
# User / Identity
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IdentityResponse:
    """One linked identity for a user (e.g. google, github, email)."""
    provider: str                     # "email" | "oauth"
    oauth_provider: Optional[str]     # "google" | "github" | None
    provider_id: str
    linked_at: datetime


@dataclass(frozen=True)
class AuthenticatedUserResponse:
    """Serialisable user representation returned after successful auth."""
    user_id: str
    email: str
    username: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    role: str
    status: str
    verified: bool
    identities: List[IdentityResponse] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Auth operation responses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LoginResponse:
    """Result of a successful email/password login."""
    success: bool
    user: Optional[AuthenticatedUserResponse] = None
    tokens: Optional[TokenResponse] = None
    session: Optional[SessionResponse] = None
    error: Optional[ApiError] = None


@dataclass(frozen=True)
class RegisterResponse:
    """Result of a successful registration."""
    success: bool
    user: Optional[AuthenticatedUserResponse] = None
    error: Optional[ApiError] = None
    requires_verification: bool = False


@dataclass(frozen=True)
class OAuthLoginResponse:
    """Returned by begin_oauth_login — contains the redirect URL."""
    success: bool
    authorization_url: Optional[str] = None
    error: Optional[ApiError] = None


@dataclass(frozen=True)
class OAuthCompleteResponse:
    """Returned by complete_oauth_login after the provider callback."""
    success: bool
    user: Optional[AuthenticatedUserResponse] = None
    tokens: Optional[TokenResponse] = None
    session: Optional[SessionResponse] = None
    is_new_user: bool = False
    error: Optional[ApiError] = None


@dataclass(frozen=True)
class LogoutResponse:
    """Result of a logout operation."""
    success: bool
    error: Optional[ApiError] = None


@dataclass(frozen=True)
class RefreshSessionResponse:
    """Result of a token/session refresh."""
    success: bool
    tokens: Optional[TokenResponse] = None
    session: Optional[SessionResponse] = None
    error: Optional[ApiError] = None


@dataclass(frozen=True)
class IdentityLinkResponse:
    """Returned after linking or unlinking an OAuth identity."""
    success: bool
    user: Optional[AuthenticatedUserResponse] = None
    error: Optional[ApiError] = None


@dataclass(frozen=True)
class AccessValidationResponse:
    """Result of validating an access token."""
    success: bool
    user: Optional[AuthenticatedUserResponse] = None
    token_claims: Optional[Dict[str, Any]] = None
    error: Optional[ApiError] = None
