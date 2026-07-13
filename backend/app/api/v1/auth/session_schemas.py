"""
Session Management API Schemas (Phase 9.9).

Pydantic models only — zero domain coupling.
All fields are derived from SessionManagementService DTOs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SessionInfoSchema(BaseModel):
    session_id: str = Field(..., examples=["sess-abc-123"])
    user_id: str
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    ip_address: Optional[str] = Field(None, examples=["192.168.1.1"])
    user_agent: Optional[str] = None
    is_expired: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: List[SessionInfoSchema]
    total: int


class RevokeSessionResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    revoked_count: Optional[int] = None
    message: str = "Session(s) revoked."
