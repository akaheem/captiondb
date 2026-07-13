"""
Health and Observability Schemas.
Standardized response formats for liveness, readiness, and application metadata.
"""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    """Represents the status of an external dependency or internal component."""
    status: str = Field(..., description="Status identifier (e.g. 'ok', 'degraded', 'not_configured', 'failed')")
    details: Optional[str] = Field(None, description="Optional diagnostic details. Must never contain secrets.")


class HealthResponse(BaseModel):
    """Standardized response for liveness probes."""
    status: str = Field(..., description="Overall application status (e.g., 'ok').")
    service: str = Field(..., description="Name of the service.")
    version: str = Field(..., description="Current running version.")
    environment: str = Field(..., description="Deployment environment (e.g., production, development).")
    timestamp: datetime = Field(..., description="Current server UTC timestamp.")
    uptime_seconds: float = Field(..., description="Number of seconds since the application started.")


class ReadinessResponse(HealthResponse):
    """Standardized response for readiness probes, including component dependency checks."""
    components: Dict[str, ComponentStatus] = Field(
        ..., 
        description="Dictionary mapping component names (database, storage, etc.) to their readiness status."
    )


class AppInfoResponse(BaseModel):
    """Standardized application metadata. Safe for public or internal dashboard consumption."""
    application_name: str
    version: str
    environment: str
    python_version: str
    build_info: Optional[str] = Field(None, description="Injected CI/CD build hash or timestamp.")
