from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "captiondb_tasks",
    broker=settings.tasks.broker_url,
    backend=settings.tasks.result_backend
)

# Optional: Configure basic celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # When testing or local, it can be useful to run synchronously, but in prod we rely on workers
    task_always_eager=False,
)

# Autodiscover tasks from the workers package
celery_app.autodiscover_tasks(["app.infrastructure.tasks.workers"])
