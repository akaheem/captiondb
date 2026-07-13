from typing import Optional
from celery.result import AsyncResult
from app.domain.interfaces.task_dispatcher import AbstractTaskDispatcher
from app.domain.models.task import (
    TaskIdentifier, 
    TaskMetadata, 
    TaskResult, 
    TaskStatus, 
    TaskProgress, 
    TaskStatistics
)
from app.infrastructure.tasks.celery_app import celery_app

class CeleryTaskDispatcher(AbstractTaskDispatcher):
    """
    Celery implementation of the AbstractTaskDispatcher.
    Translates Domain concepts into Celery primitives safely.
    """
    
    def _map_celery_state_to_task_status(self, celery_state: str) -> TaskStatus:
        mapping = {
            "PENDING": TaskStatus.QUEUED,
            "STARTED": TaskStatus.RUNNING,
            "RETRY": TaskStatus.RETRYING,
            "SUCCESS": TaskStatus.COMPLETED,
            "FAILURE": TaskStatus.FAILED,
            "REVOKED": TaskStatus.CANCELLED,
        }
        return mapping.get(celery_state, TaskStatus.FAILED)
        
    async def dispatch(self, project_id: str, metadata: TaskMetadata) -> TaskIdentifier:
        """
        Submits the video processing task to Celery.
        """
        # "process_video" will be registered by the worker later.
        async_result = celery_app.send_task(
            "process_video",
            args=[project_id],
            kwargs={"configuration": metadata.configuration}
        )
        return TaskIdentifier(task_id=async_result.id, project_id=project_id)
        
    async def get_status(self, task_id: str) -> TaskResult:
        """
        Fetches the task state from Celery's result backend.
        """
        result = AsyncResult(task_id, app=celery_app)
        status = self._map_celery_state_to_task_status(result.state)
        
        # Try to pull progress/meta from Celery's custom info if it's running
        percent = 0.0
        step = None
        error_msg = None
        
        if status == TaskStatus.RUNNING and isinstance(result.info, dict):
            percent = result.info.get("percent_complete", 0.0)
            step = result.info.get("current_step", None)
            
        elif status == TaskStatus.FAILED:
            error_msg = str(result.info) if result.info else "Unknown Celery Failure"
            
        return TaskResult(
            identifier=TaskIdentifier(task_id=task_id, project_id="unknown_from_status_poll"),
            status=status,
            progress=TaskProgress(percent_complete=percent, current_step=step),
            statistics=TaskStatistics(),
            metadata=TaskMetadata(),
            error_message=error_msg
        )
        
    async def cancel(self, task_id: str) -> bool:
        """
        Revokes a Celery task.
        """
        celery_app.control.revoke(task_id, terminate=True)
        return True
