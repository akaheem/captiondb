import logging
from app.domain.interfaces.task_dispatcher import AbstractTaskDispatcher
from app.domain.models.task import TaskIdentifier, TaskMetadata, TaskResult

logger = logging.getLogger(__name__)

class BackgroundTaskService:
    """
    Coordinates submission of background jobs.
    This service acts as the Application layer boundary over the TaskDispatcher interface.
    """
    
    def __init__(self, dispatcher: AbstractTaskDispatcher):
        self._dispatcher = dispatcher
        
    async def submit_video_processing(self, project_id: str, configuration: dict) -> TaskIdentifier:
        """
        Submit a video processing task to the queue.
        """
        metadata = TaskMetadata(configuration=configuration)
        
        logger.info(f"Submitting video processing task for project {project_id}")
        task_id = await self._dispatcher.dispatch(project_id, metadata)
        logger.info(f"Task submitted successfully. Task ID: {task_id.task_id}")
        
        return task_id
        
    async def get_task_status(self, task_id: str) -> TaskResult:
        """
        Retrieve the current status of a submitted task.
        """
        return await self._dispatcher.get_status(task_id)
        
    async def cancel_task(self, task_id: str) -> bool:
        """
        Attempt to cancel a running or queued task.
        """
        return await self._dispatcher.cancel(task_id)
