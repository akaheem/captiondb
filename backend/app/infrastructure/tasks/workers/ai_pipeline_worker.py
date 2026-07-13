import asyncio
import logging
from app.infrastructure.tasks.celery_app import celery_app
from app.infrastructure.tasks.workers.task_registry import get_ai_pipeline_context

logger = logging.getLogger(__name__)

async def _execute_pipeline(project_id: str, configuration: dict) -> dict:
    """
    Async wrapper for executing the AI Pipeline.
    """
    async with get_ai_pipeline_context() as ai_pipeline:
        # Configuration is parsed into PipelineContext dynamically
        # For now, we will construct a context dictionary or object as needed by AIPipelineService
        from app.domain.services.ai_pipeline import PipelineContext
        context = PipelineContext(
            project_id=project_id,
            options=configuration
        )
        await ai_pipeline.process(context)
        
        # PipelineService persists state directly to DB, 
        # but we also return a basic success object to Celery backend.
        return {"project_id": project_id, "status": "COMPLETED"}


@celery_app.task(bind=True, name="process_video", max_retries=3)
def process_video_task(self, project_id: str, configuration: dict):
    """
    Celery task wrapper for executing the AI Video Processing pipeline.
    Runs strictly as an orchestrator, utilizing asyncio.run to execute the async domain logic.
    """
    logger.info(f"Starting background processing for project {project_id}")
    
    try:
        # Execute the async application service
        result = asyncio.run(_execute_pipeline(project_id, configuration))
        logger.info(f"Background processing completed for project {project_id}")
        return result
        
    except Exception as e:
        logger.error(f"Background processing failed for project {project_id}: {str(e)}")
        # If it's a retryable error (e.g., transient network failure to AI Provider), retry.
        # For simplicity, we trigger a retry on any unexpected exception.
        # The AIProviderException could be used here to distinguish retryable vs fatal.
        raise self.retry(exc=e, countdown=60)
