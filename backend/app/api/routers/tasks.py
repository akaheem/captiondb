from fastapi import APIRouter, Depends, HTTPException, status
from app.api.schemas.task import TaskResponse, TaskProgressSnapshotSchema, TaskStatisticsSchema
from app.services.task_monitoring import TaskMonitoringService
from app.dependencies.services import get_task_monitoring_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])

def _build_task_response(snapshot, history=None) -> TaskResponse:
    return TaskResponse(
        task_id=snapshot.task_id,
        status=snapshot.status,
        percent_complete=snapshot.percent_complete,
        current_step=snapshot.current_step,
        error_message=snapshot.error_message,
        updated_at=snapshot.updated_at,
        statistics=TaskStatisticsSchema(
            retry_count=history.statistics.retry_count,
            time_in_queue_ms=history.statistics.time_in_queue_ms,
            execution_time_ms=history.statistics.execution_time_ms
        ) if history else None,
        history=[
            TaskProgressSnapshotSchema(
                task_id=snap.task_id,
                status=snap.status,
                percent_complete=snap.percent_complete,
                current_step=snap.current_step,
                error_message=snap.error_message,
                updated_at=snap.updated_at
            ) for snap in history.snapshots
        ] if history else None
    )


@router.get("/{task_id}", response_model=TaskResponse)
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


@router.get("/{task_id}/progress", response_model=TaskResponse)
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


@router.get("/{task_id}/history", response_model=TaskResponse)
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


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cleanup_task(
    task_id: str,
    monitoring_service: TaskMonitoringService = Depends(get_task_monitoring_service)
):
    """
    Cleans up the task monitoring state from the cache.
    Does NOT revoke the Celery worker task itself, as the monitoring service is the API's
    source of truth for task state. Worker cancellation is handled by a separate flow.
    """
    # Ensure task exists before deleting
    snapshot = await monitoring_service.get_task_status(task_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await monitoring_service.cleanup_task(task_id)
