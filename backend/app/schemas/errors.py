"""
Error response schemas for the API.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ErrorResponse(BaseModel):
    """Standardized error response format for all API errors."""
    error_code: str = Field(..., description="A unique string identifying the type of error.")
    message: str = Field(..., description="A safe, human-readable error message.")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional context about the error. Stripped in production.")
    correlation_id: Optional[str] = Field(None, description="The request correlation ID for distributed tracing.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        description="UTC timestamp of the error occurrence."
    )
