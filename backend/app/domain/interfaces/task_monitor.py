from abc import ABC, abstractmethod
from typing import Optional
from app.domain.models.task_monitor import TaskProgressSnapshot, TaskHistory

class AbstractTaskMonitor(ABC):
    """
    Abstract interface for persisting and retrieving task progress and history.
    This separates the domain's tracking logic from the underlying storage mechanism
    (e.g., Redis, In-Memory, etc.).
    """
    
    @abstractmethod
    async def save_snapshot(self, snapshot: TaskProgressSnapshot) -> None:
        """Saves a new point-in-time snapshot of the task's state."""
        pass
        
    @abstractmethod
    async def get_latest_snapshot(self, task_id: str) -> Optional[TaskProgressSnapshot]:
        """Retrieves the most recent state of the given task."""
        pass
        
    @abstractmethod
    async def get_history(self, task_id: str) -> TaskHistory:
        """Retrieves the full chronological history of the given task."""
        pass

    @abstractmethod
    async def cleanup(self, task_id: str) -> None:
        """Removes all tracking data for the given task."""
        pass
