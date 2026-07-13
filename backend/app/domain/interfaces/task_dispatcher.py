from abc import ABC, abstractmethod
from app.domain.models.task import TaskIdentifier, TaskMetadata, TaskResult

class AbstractTaskDispatcher(ABC):
    """
    Abstract interface for dispatching background tasks.
    Implementations could be Celery, RabbitMQ, Dramatiq, etc.
    """
    
    @abstractmethod
    async def dispatch(self, project_id: str, metadata: TaskMetadata) -> TaskIdentifier:
        """
        Submit a new task to the queue.
        """
        pass
        
    @abstractmethod
    async def get_status(self, task_id: str) -> TaskResult:
        """
        Retrieve the current status of a task from the queue.
        """
        pass
        
    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """
        Attempt to cancel a task in the queue.
        Returns True if successful, False otherwise.
        """
        pass
