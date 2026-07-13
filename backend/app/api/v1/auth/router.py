"""
Authentication API Router — /api/v1/auth

Architecture constraint:
  This router calls ONLY AuthenticationApiService.
  It must NEVER import or call:
    - AuthenticationService
    - EmailAuthenticationService
    - OAuthAuthenticationService
    - TokenService
    - SessionService

All business logic lives in the Application layer.
All orchestration lives in AuthenticationApiService.
This router's sole job: validate HTTP input → call the service → map the
result DTO to a Pydantic response schema → return HTTP.
"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from loguru import logger

from app.api.v1.auth.service import AuthenticationApiService
from app.api.v1.auth.dtos import (
    ApiError,
    AuthenticatedUserResponse,
    IdentityLinkResponse as IdentityLinkDTO,
    LoginResponse as LoginDTO,
    LogoutResponse as LogoutDTO,
    OAuthCompleteResponse,
    OAuthLoginResponse,
    RefreshSessionResponse,
    RegisterResponse as RegisterDTO,
    AccessValidationResponse,
)
from app.api.v1.auth.schemas import (
    ApiErrorSchema,
    IdentityLinkResponse,
    IdentitySchema,
    LinkIdentityRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    MeResponse,
    OAuthBeginRequest,
    OAuthBeginResponse,
    OAuthCallbackRequest,
    OAuthCallbackResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    SessionSchema,
    TokenSchema,
    UserSchema,
    ValidateResponse,
)
from app.dependencies.services import get_authentication_api_service, get_current_user
from app.domain.models.auth import OAuthProvider, User

# OpenAPI security annotation applied to every protected endpoint
_BEARER_SECURITY = [{"BearerAuth": []}]

router = APIRouter()

# ---------------------------------------------------------------------------
# ── Error-code → HTTP status mapping ────────────────────────────────────────
# ---------------------------------------------------------------------------

_ERROR_STATUS_MAP: dict[str, int] = {
    "INVALID_CREDENTIALS":    status.HTTP_401_UNAUTHORIZED,
    "AUTHENTICATION_ERROR":   status.HTTP_401_UNAUTHORIZED,
    "ACCOUNT_NOT_ACTIVE":     status.HTTP_403_FORBIDDEN,
    "TOKEN_EXPIRED":          status.HTTP_401_UNAUTHORIZED,
    "NOT_FOUND":              status.HTTP_404_NOT_FOUND,
    "CONFLICT":               status.HTTP_409_CONFLICT,
    "IDENTITY_ALREADY_LINKED": status.HTTP_409_CONFLICT,
    "IDENTITY_NOT_FOUND":     status.HTTP_404_NOT_FOUND,
    "VALIDATION_ERROR":       status.HTTP_400_BAD_REQUEST,
    "OAUTH_PROVIDER_ERROR":   status.HTTP_502_BAD_GATEWAY,
    "OAUTH_FAILED":           status.HTTP_400_BAD_REQUEST,
    "INTERNAL_ERROR":         status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def _http_status_for(error: Optional[ApiError]) -> int:
    if error is None:
        return status.HTTP_200_OK
    return _ERROR_STATUS_MAP.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)


def _map_error(error: Optional[ApiError]) -> Optional[ApiErrorSchema]:
    if error is None:
        return None
    return ApiErrorSchema(code=error.code, message=error.message, details=error.details)


def _map_user(user: Optional[AuthenticatedUserResponse]) -> Optional[UserSchema]:
    if user is None:
        return None
    return UserSchema(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        role=user.role,
        status=user.status,
        verified=user.verified,
        identities=[
            IdentitySchema(
                provider=i.provider,
                oauth_provider=i.oauth_provider,
                provider_id=i.provider_id,
                linked_at=i.linked_at,
            )
            for i in user.identities
        ],
    )


def _map_token(tokens) -> Optional[TokenSchema]:
    if tokens is None:
        return None
    return TokenSchema(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
    )


def _map_session(session) -> Optional[SessionSchema]:
    if session is None:
        return None
    return SessionSchema(
        session_id=session.session_id,
        user_id=session.user_id,
        created_at=session.created_at,
    )


def _user_to_dto(user: "User") -> "AuthenticatedUserResponse":
    """Convert a domain User (from get_current_user) to an API DTO."""
    from app.api.v1.auth.dtos import AuthenticatedUserResponse, IdentityResponse
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


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    """Extract the raw token from 'Bearer <token>' header value."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def _resolve_provider(provider: str) -> OAuthProvider:
    """Resolve a URL slug to an OAuthProvider enum, raise 400 if unknown."""
    try:
        return OAuthProvider(provider.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown OAuth provider: '{provider}'. Supported: {[p.value for p in OAuthProvider]}",
        )


# ---------------------------------------------------------------------------
# ── Email / Password Endpoints ───────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    tags=["auth"],
    responses={
        201: {"description": "User registered successfully."},
        400: {"description": "Weak password or validation error."},
        409: {"description": "Email or username already in use."},
        422: {"description": "Request body validation failed."},
    },
)
async def register(
    body: RegisterRequest,
    auth_api: AuthenticationApiService = Depends(get_authentication_api_service),
) -> RegisterResponse:
    """
    Register a new user account with email and password.

    Returns the created user profile.  If email verification is required,
    ``requires_verification`` will be ``true`` and the user should check their inbox.
    """
    logger.info(f"POST /register — email={body.email}")
    result: RegisterDTO = await auth_api.register_email(body.email, body.username, body.password)

    http_status = status.HTTP_201_CREATED if result.success else _http_status_for(result.error)
    response = RegisterResponse(
        success=result.success,
        user=_map_user(result.user),
        requires_verification=result.requires_verification,
        error=_map_error(result.error),
    )
    if not result.success:
        raise HTTPException(status_code=http_status, detail=response.model_dump())
    return response


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login with email and password",
    tags=["auth"],
    responses={
        200: {"description": "Authenticated successfully."},
        401: {"description": "Invalid credentials or inactive account."},
        422: {"description": "Request body validation failed."},
    },
)
async def login(
    body: LoginRequest,
    request: Request,
    auth_api: AuthenticationApiService = Depends(get_authentication_api_service),
) -> LoginResponse:
    """
    Authenticate with email + password.

    Returns access tokens and a session handle on success.
    Credentials are never logged — only a masked email appears in logs.
    """
    logger.info(f"POST /login — email={body.email}")
    session_meta = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    result: LoginDTO = await auth_api.login_email(body.email, body.password, session_meta)

    if not result.success:
        raise HTTPException(
            status_code=_http_status_for(result.error),
            detail=_map_error(result.error).model_dump(),
        )
    return LoginResponse(
        success=True,
        user=_map_user(result.user),
        tokens=_map_token(result.tokens),
        session=_map_session(result.session),
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout and revoke session",
    tags=["auth"],
    responses={
        200: {"description": "Logged out successfully."},
        401: {"description": "Missing or invalid token."},
    },
)
async def logout(
    body: LogoutRequest,
    authorization: Annotated[Optional[str], Header()] = None,
    auth_api: AuthenticationApiService = Depends(get_authentication_api_service),
) -> LogoutResponse:
    """
    Revoke the current access token and terminate the session.

    Pass the Bearer token in the ``Authorization`` header.
    """
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token.")

    result: LogoutDTO = await auth_api.logout(token, session_id=body.session_id)
    if not result.success:
        raise HTTPException(
            status_code=_http_status_for(result.error),
            detail=_map_error(result.error).model_dump(),
        )
    return LogoutResponse(success=True)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
    tags=["auth"],
    responses={
        200: {"description": "Tokens refreshed."},
        401: {"description": "Token invalid or expired."},
    },
)
async def refresh_session(
    body: RefreshRequest,
    authorization: Annotated[Optional[str], Header()] = None,
    auth_api: AuthenticationApiService = Depends(get_authentication_api_service),
) -> RefreshResponse:
    """Extend a valid session and receive a fresh token."""
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token.")

    result: RefreshSessionResponse = await auth_api.refresh_session(token, session_id=body.session_id)
    if not result.success:
        raise HTTPException(
            status_code=_http_status_for(result.error),
            detail=_map_error(result.error).model_dump(),
        )
    return RefreshResponse(
        success=True,
        tokens=_map_token(result.tokens),
        session=_map_session(result.session),
    )


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current authenticated user",
    tags=["auth"],
    openapi_extra={"security": [{"BearerAuth": []}]},
    responses={
        200: {"description": "Returns the current user profile."},
        401: {"description": "Token missing or invalid."},
    },
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> MeResponse:
    """
    Returns the profile of the currently authenticated user.

    Authentication is enforced by the ``get_current_user`` dependency —
    the middleware has already validated the token before this runs.
    """
    return MeResponse(user=_map_user(_user_to_dto(current_user)))


# ---------------------------------------------------------------------------
# ── OAuth Endpoints ──────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.post(
    "/oauth/{provider}/begin",
    response_model=OAuthBeginResponse,
    summary="Start OAuth login flow",
    tags=["auth", "oauth"],
    responses={
        200: {"description": "Returns the provider authorization URL."},
        400: {"description": "Unknown provider or missing state."},
    },
)
async def oauth_begin(
    provider: str,
    body: OAuthBeginRequest,
    auth_api: AuthenticationApiService = Depends(get_authentication_api_service),
) -> OAuthBeginResponse:
    """
    Returns the authorization URL the client should redirect to.

    The ``state`` parameter must be generated by the client and stored in
    session/cookie for CSRF validation in the callback step.
    """
    provider_enum = _resolve_provider(provider)
    result: OAuthLoginResponse = await auth_api.begin_oauth_login(
        provider_enum, body.state, body.redirect_uri
    )
    if not result.success:
        raise HTTPException(
            status_code=_http_status_for(result.error),
            detail=_map_error(result.error).model_dump(),
        )
    return OAuthBeginResponse(success=True, authorization_url=result.authorization_url)


@router.get(
    "/oauth/{provider}/callback",
    response_model=OAuthCallbackResponse,
    summary="Complete OAuth login (provider callback)",
    tags=["auth", "oauth"],
    responses={
        200: {"description": "OAuth login completed."},
        400: {"description": "Invalid code or state."},
        502: {"description": "OAuth provider returned an error."},
    },
)
async def oauth_callback(
    provider: str,
    request: Request,
    code: str = Query(..., description="Authorization code from the provider."),
    state: str = Query(..., description="State token for CSRF validation."),
    redirect_uri: str = Query(...),
    auth_api: AuthenticationApiService = Depends(get_authentication_api_service),
) -> OAuthCallbackResponse:
    """
    Handles the OAuth provider redirect.

    Exchanges the authorization code for tokens, retrieves the user profile,
    and creates a CaptionDB session.  New users are provisioned automatically.

    **Security**: The ``state`` parameter must be validated against the value
    stored by the client before calling this endpoint.
    """
    provider_enum = _resolve_provider(provider)
    logger.info(f"GET /oauth/{provider}/callback — state={state[:8]}…")

    session_meta = {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
    result: OAuthCompleteResponse = await auth_api.complete_oauth_login(
        provider_enum, code, redirect_uri, session_meta
    )
    if not result.success:
        raise HTTPException(
            status_code=_http_status_for(result.error),
            detail=_map_error(result.error).model_dump(),
        )
    return OAuthCallbackResponse(
        success=True,
        user=_map_user(result.user),
        tokens=_map_token(result.tokens),
        session=_map_session(result.session),
        is_new_user=result.is_new_user,
    )


# ---------------------------------------------------------------------------
# ── Identity Management Endpoints ────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.post(
    "/identity/link",
    response_model=IdentityLinkResponse,
    summary="Link an OAuth identity to the current account",
    tags=["auth", "identity"],
    openapi_extra={"security": [{"BearerAuth": []}]},
    responses={
        200: {"description": "Identity linked successfully."},
        401: {"description": "Not authenticated."},
        409: {"description": "Identity already linked."},
        502: {"description": "OAuth provider error."},
    },
)
async def link_identity(
    body: LinkIdentityRequest,
    current_user: User = Depends(get_current_user),
    auth_api: AuthenticationApiService = Depends(get_authentication_api_service),
) -> IdentityLinkResponse:
    """
    Link an additional OAuth identity (e.g. Google) to the current account.

    Authentication is enforced by the ``get_current_user`` dependency.
    """
    provider_enum = _resolve_provider(body.provider)
    result: IdentityLinkDTO = await auth_api.link_identity(
        current_user, provider_enum, body.code, body.redirect_uri
    )
    if not result.success:
        raise HTTPException(
            status_code=_http_status_for(result.error),
            detail=_map_error(result.error).model_dump(),
        )
    return IdentityLinkResponse(success=True, user=_map_user(result.user))


@router.delete(
    "/identity/{provider}",
    response_model=IdentityLinkResponse,
    summary="Unlink an OAuth identity",
    tags=["auth", "identity"],
    openapi_extra={"security": [{"BearerAuth": []}]},
    responses={
        200: {"description": "Identity unlinked."},
        400: {"description": "Cannot unlink the last identity."},
        401: {"description": "Not authenticated."},
        404: {"description": "Identity not found."},
    },
)
async def unlink_identity(
    provider: str,
    current_user: User = Depends(get_current_user),
    auth_api: AuthenticationApiService = Depends(get_authentication_api_service),
) -> IdentityLinkResponse:
    """
    Unlink an OAuth identity from the current account.

    At least one identity must remain.
    Authentication is enforced by the ``get_current_user`` dependency.
    """
    provider_enum = _resolve_provider(provider)
    result: IdentityLinkDTO = await auth_api.unlink_identity(current_user, provider_enum)
    if not result.success:
        raise HTTPException(
            status_code=_http_status_for(result.error),
            detail=_map_error(result.error).model_dump(),
        )
    return IdentityLinkResponse(success=True, user=_map_user(result.user))


# ---------------------------------------------------------------------------
# ── Token Validation ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.get(
    "/validate",
    response_model=ValidateResponse,
    summary="Validate an access token",
    tags=["auth"],
    responses={
        200: {"description": "Token is valid."},
        401: {"description": "Token invalid or expired."},
    },
)
async def validate_token(
    authorization: Annotated[Optional[str], Header()] = None,
    auth_api: AuthenticationApiService = Depends(get_authentication_api_service),
) -> ValidateResponse:
    """
    Validate an access token and return the associated claims and user.

    Used by API gateways and internal middleware stubs.
    """
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token.")

    result: AccessValidationResponse = await auth_api.validate_access(token)
    if not result.success:
        raise HTTPException(
            status_code=_http_status_for(result.error),
            detail=_map_error(result.error).model_dump(),
        )
    return ValidateResponse(
        success=True,
        user=_map_user(result.user),
        token_claims=result.token_claims,
    )
