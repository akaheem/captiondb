"""
System endpoints for health, readiness, and observability.
"""
import sys
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request

from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse, ReadinessResponse, AppInfoResponse, ComponentStatus

router = APIRouter()


def _get_uptime(request: Request) -> float:
    """Safely calculates uptime in seconds based on the lifespan startup hook."""
    startup_time: datetime = getattr(request.app.state, "startup_time", datetime.now(timezone.utc))
    return (datetime.now(timezone.utc) - startup_time).total_seconds()


@router.get("/", response_model=Dict[str, Any])
async def root(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Root endpoint returning minimal project information.
    """
    return {
        "project": settings.app.name,
        "version": settings.app.version,
        "environment": settings.app.environment,
        "status": "online"
    }


@router.get("/health/live", response_model=HealthResponse)
async def liveness_probe(request: Request, settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Liveness probe. Indicates if the application is running and able to accept HTTP requests.
    Used by orchestrators (like Kubernetes or Docker) to restart dead containers.
    No deep component checks are performed here to avoid cascade failures.
    """
    return HealthResponse(
        status="ok",
        service=settings.app.name,
        version=settings.app.version,
        environment=settings.app.environment,
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=_get_uptime(request)
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_probe(request: Request, settings: Settings = Depends(get_settings)) -> ReadinessResponse:
    """
    Readiness probe. Indicates if the application is fully ready to process business traffic.
    Used by load balancers to route traffic.
    Currently returns 'not_configured' for external systems since they are not implemented in Phase 1.
    """
    return ReadinessResponse(
        status="ok",
        service=settings.app.name,
        version=settings.app.version,
        environment=settings.app.environment,
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=_get_uptime(request),
        components={
            "storage": ComponentStatus(status="not_configured", details="Storage adapter not yet wired to readiness"),
            "database": ComponentStatus(status="not_configured", details="Database dependency not yet implemented"),
            "ai_provider": ComponentStatus(status="not_configured", details="AI Provider dependency not yet implemented"),
            "cache": ComponentStatus(status="not_configured", details="Cache dependency not yet implemented")
        }
    )


@router.get("/health/info", response_model=AppInfoResponse)
async def app_info(settings: Settings = Depends(get_settings)) -> AppInfoResponse:
    """
    Application information exposing safe metadata.
    Strictly forbids exposing internal configuration, secrets, or internal network topology.
    """
    return AppInfoResponse(
        application_name=settings.app.name,
        version=settings.app.version,
        environment=settings.app.environment,
        python_version=sys.version.split(" ")[0],
        build_info="local_build"  # In a real CI/CD pipeline, this would map to a commit hash or build ID
    )
