from fastapi import APIRouter, Depends, HTTPException, status
from app.api.schemas.task import TaskResponse, TaskProgressSnapshotSchema, TaskStatisticsSchema
from app.services.task_monitoring import TaskMonitoringService
from app.dependencies.services import get_task_monitoring_service

router = APIRouter()

def _build_task_response(snapshot, history=None) -> TaskResponse:
    # Build statistics block
    stats_schema = None
    if history and history.statistics:
        stats_schema = TaskStatisticsSchema(
            retry_count=history.statistics.retry_count,
            time_in_queue_ms=history.statistics.time_in_queue_ms,
            execution_time_ms=history.statistics.execution_time_ms
        )
        
    # Build history block
    history_schema = None
    if history:
        history_schema = [
            TaskProgressSnapshotSchema(
                task_id=snap.task_id,
                status=snap.status,
                percent_complete=snap.percent_complete,
                current_step=snap.current_step,
                error_message=snap.error_message,
                updated_at=snap.updated_at
            ) for snap in history.snapshots
        ]
        
    return TaskResponse(
        task_id=snapshot.task_id,
        status=snapshot.status,
        progress=snapshot.percent_complete,
        current_stage=snapshot.current_step,
        updated_at=snapshot.updated_at,
        error_message=snapshot.error_message,
        # Stubbing out future fields not yet stored in snapshot
        created_at=None,
        started_at=None,
        completed_at=None,
        duration_seconds=None,
        retry_count=stats_schema.retry_count if stats_schema else 0,
        metadata=None,
        statistics=stats_schema,
        history=history_schema
    )


@router.get("/{task_id}", response_model=TaskResponse, summary="Get Task Status")
async def get_task(
    task_id: str,
    monitoring_service: TaskMonitoringService = Depends(get_task_monitoring_service)
):
    """
    Retrieves the full task metadata, including its history and statistics.
    """
    snapshot = await monitoring_service.get_task_status(task_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Task not found")
        
    history = await monitoring_service.get_task_history(task_id)
    return _build_task_response(snapshot, history)


@router.get("/{task_id}/progress", response_model=TaskResponse, summary="Get Task Progress")
async def get_task_progress(
    task_id: str,
    monitoring_service: TaskMonitoringService = Depends(get_task_monitoring_service)
):
    """
    Retrieves the current progress snapshot for the task (omits history for a lighter response).
    """
    snapshot = await monitoring_service.get_task_status(task_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return _build_task_response(snapshot, history=None)


@router.get("/{task_id}/history", response_model=TaskResponse, summary="Get Task History")
async def get_task_history(
    task_id: str,
    monitoring_service: TaskMonitoringService = Depends(get_task_monitoring_service)
):
    """
    Retrieves the task history and current status. Identical to GET /{task_id}, 
    but explicit for clients explicitly requesting history.
    """
    snapshot = await monitoring_service.get_task_status(task_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Task not found")
        
    history = await monitoring_service.get_task_history(task_id)
    return _build_task_response(snapshot, history)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Cleanup Task")
async def cleanup_task(
    task_id: str,
    monitoring_service: TaskMonitoringService = Depends(get_task_monitoring_service)
):
    """
    Cleans up the task monitoring state from the cache.
    Does NOT revoke the Celery worker task itself, as the monitoring service is the API's
    source of truth for task state. Worker cancellation is handled by a separate flow.
    """
    snapshot = await monitoring_service.get_task_status(task_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await monitoring_service.cleanup_task(task_id)
