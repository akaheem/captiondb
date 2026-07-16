"""
CaptionDB Backend Entrypoint.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware
from loguru import logger

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.api.exception_handlers import setup_exception_handlers
from app.api.middleware import LoggingMiddleware
from app.api.router import global_api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    Executes startup and shutdown logic.
    """
    from datetime import datetime, timezone
    app.state.startup_time = datetime.now(timezone.utc)
    
    setup_logging()
    settings = get_settings()
    logger.info(f"Starting up {settings.app.name} v{settings.app.version} in {settings.app.environment} mode...")
    
    # FUTURE INTEGRATION: OpenTelemetry / Prometheus setup would be initialized here.
    
    yield
    
    # FUTURE INTEGRATION: OpenTelemetry / Prometheus teardown would happen here.
    logger.info(f"Shutting down {settings.app.name}...")


def create_app() -> FastAPI:
    """
    FastAPI application factory.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        openapi_url=f"{settings.api.v1_prefix}/openapi.json",
        lifespan=lifespan,
        # ── OpenAPI Bearer Security Scheme ───────────────────────────
        # Protected endpoints decorated with security=[{"BearerAuth": []}]
        # will display a lock icon in /docs.
        swagger_ui_parameters={"persistAuthorization": True},
    )

    # Register global exception handlers
    setup_exception_handlers(app)

    # Add Correlation ID middleware for request tracing (outermost)
    app.add_middleware(CorrelationIdMiddleware)

    # ── AuthenticationMiddleware ─────────────────────────────────────
    # Must run AFTER CorrelationIdMiddleware (inner in ASGI stack = added after)
    # so the correlation ID is already set when we log auth events.
    # Must run BEFORE LoggingMiddleware so logging can read user_id from state.
    from app.services.authorization import AuthorizationService
    from app.infrastructure.auth.middleware import AuthenticationMiddleware
    from app.dependencies.services import (
        get_token_service,
        get_user_provider,
        get_session_service,
    )
    from app.dependencies.infrastructure import get_settings as _get_settings

    # Build a single AuthorizationService for the app lifetime.
    # Its sub-services are also singletons created here to share connection pools.
    #
    # ── Boot shim (local preview) ────────────────────────────────────
    # The auth providers (user/token/session) are not yet implemented and
    # raise NotImplementedError. Rather than crash at startup, we skip the
    # AuthenticationMiddleware when any provider is absent, allowing the app
    # to boot and serve public/non-auth-guarded endpoints. This changes the
    # runtime security posture and is intended for local development only.
    try:
        _settings = get_settings()
        _token_svc = get_token_service()
        _user_prov = get_user_provider()
        _session_svc = get_session_service()
        _authz_svc = AuthorizationService(
            token_service=_token_svc,
            user_provider=_user_prov,
            session_service=_session_svc,
        )
        app.add_middleware(AuthenticationMiddleware, authorization_service=_authz_svc)
    except NotImplementedError as exc:
        logger.warning(
            "AuthenticationMiddleware disabled (boot shim): {}. "
            "Auth-guarded endpoints will not be protected. "
            "Do not use this configuration in production.",
            exc,
        )

    # Add custom Logging and Timing middleware
    app.add_middleware(LoggingMiddleware)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.cors.allowed_methods,
        allow_headers=settings.cors.allowed_headers,
    )

    # ── OpenAPI Security Scheme ──────────────────────────────────────
    def _custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        from fastapi.openapi.utils import get_openapi
        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})
        schema["components"]["securitySchemes"]["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your access token obtained from /api/v1/auth/login or /api/v1/auth/oauth/{provider}/callback",
        }
        app.openapi_schema = schema
        return schema
    
    from fastapi.routing import APIRoute

    for route in app.routes:
        if isinstance(route, APIRoute):
            try:
                route.dependant
                print(f"OK: {route.path}")
            except Exception as e:
                print(f"BROKEN: {route.path}")
                raise
    app.openapi = _custom_openapi

    # Register global API router (versioning prefixes are handled internally)
    app.include_router(global_api_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.api.host, port=settings.api.port, reload=True)
