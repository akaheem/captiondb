"""
AuthenticationMiddleware — ASGI middleware.

Responsibilities:
  • Read the Authorization header from every incoming request.
  • Extract the Bearer token (or detect its absence).
  • Delegate ALL validation to AuthorizationService (no JWT/token parsing here).
  • Attach the resulting RequestContext to request.state.auth_context.
  • Always call next(request) — anonymous endpoints remain accessible.
  • Never expose provider details, token contents, or stack traces in responses.

Design:
  - Gracefully handles missing tokens (attaches an anonymous context).
  - Gracefully handles malformed headers (attaches anonymous context + logs).
  - Hard authentication failures (expired/invalid token) attach an anonymous
    context with an error hint — the DI layer raises 401 when required.
  - Uses a single AuthorizationService instance (injected at startup) to
    avoid rebuilding sub-services per request.

Registration order (main.py):
    CorrelationIdMiddleware          ← outermost
    AuthenticationMiddleware         ← reads token, writes request.state
    LoggingMiddleware                ← can log user_id from state
    CORSMiddleware
"""
from __future__ import annotations

import re
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from loguru import logger

try:
    from asgi_correlation_id import correlation_id as _correlation_id_ctx
    def _get_correlation_id() -> Optional[str]:
        return _correlation_id_ctx.get()
except ImportError:
    def _get_correlation_id() -> Optional[str]:
        return None

from app.core.exceptions import AuthenticationException, AccountNotActiveException, TokenExpiredException
from app.domain.models.request_context import RequestContext
from app.services.authorization import AuthorizationService

# Regex: exactly "Bearer <token>" — one space, printable chars only
_BEARER_RE = re.compile(r"^Bearer ([A-Za-z0-9\-_.~+/]+=*)$")

# Paths that should never trigger authentication errors in the middleware.
# The middleware *always* passes through, but these paths get nicer logging.
_ANONYMOUS_PATHS = frozenset({
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/oauth",
    "/api/v1/system",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
})


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that performs Bearer token validation and attaches a
    RequestContext to every request before it reaches a router.

    Injected once at application startup — AuthorizationService and all
    its dependencies are reused across requests.
    """

    def __init__(self, app, authorization_service: AuthorizationService) -> None:
        super().__init__(app)
        self._authz = authorization_service

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        correlation_id = _get_correlation_id()

        # 1. Extract token from Authorization header
        token = self._extract_bearer(request)

        if token is None:
            # No Authorization header or non-Bearer scheme — anonymous context
            request.state.auth_context = RequestContext.anonymous(
                correlation_id=correlation_id
            )
            return await call_next(request)

        # 2. Delegate ALL validation to AuthorizationService
        try:
            context = await self._authz.build_context(
                bearer_token=token,
                correlation_id=correlation_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            request.state.auth_context = context

        except TokenExpiredException as exc:
            logger.info(
                f"[{correlation_id}] Token expired — attaching anonymous context."
            )
            request.state.auth_context = RequestContext.anonymous(
                correlation_id=correlation_id
            )
            # Store the error code so DI can surface it as 401
            request.state.auth_error = "TOKEN_EXPIRED"

        except AccountNotActiveException as exc:
            logger.warning(
                f"[{correlation_id}] Inactive account attempted access: {exc.error_code}"
            )
            request.state.auth_context = RequestContext.anonymous(
                correlation_id=correlation_id
            )
            request.state.auth_error = "ACCOUNT_NOT_ACTIVE"

        except AuthenticationException as exc:
            logger.info(
                f"[{correlation_id}] Authentication failed: {exc.error_code}"
            )
            request.state.auth_context = RequestContext.anonymous(
                correlation_id=correlation_id
            )
            request.state.auth_error = "AUTHENTICATION_ERROR"

        except Exception as exc:
            # Unexpected error — log fully but never surface details
            logger.exception(
                f"[{correlation_id}] Unexpected middleware auth error: {exc}"
            )
            request.state.auth_context = RequestContext.anonymous(
                correlation_id=correlation_id
            )
            request.state.auth_error = "INTERNAL_ERROR"

        return await call_next(request)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_bearer(request: Request) -> Optional[str]:
        """
        Parse the Authorization header.

        Returns the raw token string on success, None otherwise.
        Logs a warning for malformed headers (present but wrong format).
        """
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if not auth_header:
            return None

        match = _BEARER_RE.match(auth_header)
        if match:
            return match.group(1)

        # Header present but malformed — log but don't block
        safe_preview = auth_header[:20] + "…" if len(auth_header) > 20 else auth_header
        logger.warning(
            f"Malformed Authorization header received: '{safe_preview}' — "
            "treating as anonymous."
        )
        return None
