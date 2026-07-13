import logging
from app.infrastructure.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="process_upload")
def process_upload_task(self, project_id: str, file_path: str):
    """
    Stub for a background upload processing task.
    Currently, CaptionDB handles uploads synchronously through streaming in the router,
    so this worker is just a placeholder for future async upload handling
    (e.g., fetching a video from a remote URL or S3 bucket).
    """
    logger.info(f"Background upload task stub called for project {project_id}")
    return {"project_id": project_id, "status": "COMPLETED"}
