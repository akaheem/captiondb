from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"

@dataclass
class TaskIdentifier:
    task_id: str
    project_id: str

@dataclass
class TaskProgress:
    percent_complete: float = 0.0
    current_step: Optional[str] = None

@dataclass
class TaskStatistics:
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0

@dataclass
class TaskMetadata:
    configuration: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskResult:
    identifier: TaskIdentifier
    status: TaskStatus
    progress: TaskProgress = field(default_factory=TaskProgress)
    statistics: TaskStatistics = field(default_factory=TaskStatistics)
    metadata: TaskMetadata = field(default_factory=TaskMetadata)
    error_message: Optional[str] = None
