from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.domain.models.video import VideoStatus

class ProcessingStartResponse(BaseModel):
    project_id: str = Field(..., description="The ID of the project being processed.")
    status: VideoStatus = Field(..., description="The current status after submission.")
    message: str = Field(..., description="Human-readable submission result.")

class ProcessingStatusResponse(BaseModel):
    status: VideoStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class ProcessingProgressResponse(BaseModel):
    progress_percent: float
    current_stage: Optional[str] = None
