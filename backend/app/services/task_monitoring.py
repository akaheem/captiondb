import logging
from typing import Optional
from app.domain.models.task import TaskStatus
from app.domain.models.task_monitor import TaskProgressSnapshot, TaskHistory
from app.domain.interfaces.task_monitor import AbstractTaskMonitor

logger = logging.getLogger(__name__)

class TaskMonitoringService:
    """
    Centralized monitoring service for background tasks.
    Acts as the single source of truth for task progress and state, decoupling
    the application from Celery's state representation.
    """
    
    def __init__(self, monitor: AbstractTaskMonitor):
        self._monitor = monitor
        
    async def publish_queued(self, task_id: str) -> None:
        logger.info(f"Task {task_id} queued.")
        snapshot = TaskProgressSnapshot(task_id=task_id, status=TaskStatus.QUEUED)
        await self._monitor.save_snapshot(snapshot)

    async def publish_started(self, task_id: str) -> None:
        logger.info(f"Task {task_id} started processing.")
        snapshot = TaskProgressSnapshot(task_id=task_id, status=TaskStatus.RUNNING)
        await self._monitor.save_snapshot(snapshot)
        
    async def publish_progress(self, task_id: str, percent: float, step: str) -> None:
        logger.debug(f"Task {task_id} progress: {percent}% - {step}")
        snapshot = TaskProgressSnapshot(
            task_id=task_id, 
            status=TaskStatus.RUNNING,
            percent_complete=percent,
            current_step=step
        )
        await self._monitor.save_snapshot(snapshot)
        
    async def publish_completed(self, task_id: str) -> None:
        logger.info(f"Task {task_id} completed successfully.")
        snapshot = TaskProgressSnapshot(
            task_id=task_id, 
            status=TaskStatus.COMPLETED,
            percent_complete=100.0,
            current_step="Finished"
        )
        await self._monitor.save_snapshot(snapshot)
        
    async def publish_failed(self, task_id: str, error: str, retrying: bool = False) -> None:
        status = TaskStatus.RETRYING if retrying else TaskStatus.FAILED
        logger.error(f"Task {task_id} failed. Retrying: {retrying}. Error: {error}")
        snapshot = TaskProgressSnapshot(
            task_id=task_id, 
            status=status,
            error_message=error
        )
        await self._monitor.save_snapshot(snapshot)

    async def get_task_status(self, task_id: str) -> Optional[TaskProgressSnapshot]:
        """Returns the latest status snapshot for the task."""
        return await self._monitor.get_latest_snapshot(task_id)
        
    async def get_task_history(self, task_id: str) -> TaskHistory:
        """Returns the full execution history for the task."""
        return await self._monitor.get_history(task_id)
        
    async def cleanup_task(self, task_id: str) -> None:
        """Removes all tracking data for the task."""
        logger.info(f"Cleaning up task tracking data for {task_id}")
        await self._monitor.cleanup(task_id)
