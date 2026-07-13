from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.domain.models.task import TaskStatus


class TaskProgressSnapshotSchema(BaseModel):
    """Schema representing a single point-in-time snapshot of task progress."""
    task_id: str
    status: TaskStatus
    percent_complete: float = 0.0
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: datetime


class TaskStatisticsSchema(BaseModel):
    """Schema representing task metrics."""
    retry_count: int = 0
    time_in_queue_ms: Optional[float] = None
    execution_time_ms: Optional[float] = None


class TaskResponse(BaseModel):
    """
    Unified schema for Task endpoints.
    Used by /tasks/{id}, /tasks/{id}/progress, and /tasks/{id}/history.
    """
    task_id: str
    status: TaskStatus
    progress: float = Field(default=0.0, description="Percentage complete")
    current_stage: Optional[str] = Field(default=None, description="Current processing stage")
    
    # Timestamps
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    # Metrics
    duration_seconds: Optional[float] = None
    retry_count: int = 0
    
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    
    # Optional nested payloads
    statistics: Optional[TaskStatisticsSchema] = None
    history: Optional[List[TaskProgressSnapshotSchema]] = None
