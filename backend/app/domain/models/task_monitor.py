from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from app.domain.models.task import TaskStatus

def _now() -> datetime:
    return datetime.now(timezone.utc)

@dataclass
class TaskProgressSnapshot:
    """Represents a single point-in-time snapshot of task progress."""
    task_id: str
    status: TaskStatus
    percent_complete: float = 0.0
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: datetime = field(default_factory=_now)


@dataclass
class TaskStatistics:
    """Metrics regarding task execution."""
    retry_count: int = 0
    time_in_queue_ms: Optional[float] = None
    execution_time_ms: Optional[float] = None


@dataclass
class TaskHistory:
    """Chronological list of task progress snapshots."""
    task_id: str
    snapshots: List[TaskProgressSnapshot] = field(default_factory=list)
    statistics: TaskStatistics = field(default_factory=TaskStatistics)
