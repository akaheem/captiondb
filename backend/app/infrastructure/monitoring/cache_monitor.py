import json
from typing import Optional
from datetime import datetime
from app.domain.interfaces.task_monitor import AbstractTaskMonitor
from app.domain.models.task_monitor import TaskProgressSnapshot, TaskHistory, TaskStatistics
from app.domain.models.task import TaskStatus
from app.services.cache import CacheService

class CacheTaskMonitor(AbstractTaskMonitor):
    """
    TaskMonitor implementation using CacheService (Redis).
    Stores the latest snapshot in a key and appends to a history list.
    """
    
    def __init__(self, cache_service: CacheService):
        self._cache = cache_service
        self._ttl_seconds = 86400  # 24 hours
        
    def _snapshot_key(self, task_id: str) -> str:
        return f"task:snapshot:{task_id}"
        
    def _history_key(self, task_id: str) -> str:
        return f"task:history:{task_id}"
        
    async def save_snapshot(self, snapshot: TaskProgressSnapshot) -> None:
        """Saves a new snapshot to the cache."""
        # Convert snapshot to dict, handling datetime serialization
        data = {
            "task_id": snapshot.task_id,
            "status": snapshot.status.value,
            "percent_complete": snapshot.percent_complete,
            "current_step": snapshot.current_step,
            "error_message": snapshot.error_message,
            "updated_at": snapshot.updated_at.isoformat()
        }
        
        # Save latest snapshot
        await self._cache.set(
            self._snapshot_key(snapshot.task_id), 
            data, 
            ttl_seconds=self._ttl_seconds
        )
        
        # We need a list operation for history. Since CacheService doesn't have an append/rpush
        # we will fetch, append and save. This is not atomic but suffices for this phase.
        # Alternatively we can just use the provider directly if we need list operations.
        # For now, let's pull, append and push.
        history_data = await self._cache.get(self._history_key(snapshot.task_id))
        if history_data is None:
            history_data = []
            
        # Append the new data
        history_data.append(data)
        
        # Optional: Cap history size to prevent unbounded growth (e.g. 100 events)
        if len(history_data) > 100:
            history_data = history_data[-100:]
            
        await self._cache.set(
            self._history_key(snapshot.task_id),
            history_data,
            ttl_seconds=self._ttl_seconds
        )

    async def get_latest_snapshot(self, task_id: str) -> Optional[TaskProgressSnapshot]:
        data = await self._cache.get(self._snapshot_key(task_id))
        if not data:
            return None
            
        return TaskProgressSnapshot(
            task_id=data["task_id"],
            status=TaskStatus(data["status"]),
            percent_complete=data.get("percent_complete", 0.0),
            current_step=data.get("current_step"),
            error_message=data.get("error_message"),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )
        
    async def get_history(self, task_id: str) -> TaskHistory:
        history_data = await self._cache.get(self._history_key(task_id))
        snapshots = []
        if history_data:
            for data in history_data:
                snapshots.append(
                    TaskProgressSnapshot(
                        task_id=data["task_id"],
                        status=TaskStatus(data["status"]),
                        percent_complete=data.get("percent_complete", 0.0),
                        current_step=data.get("current_step"),
                        error_message=data.get("error_message"),
                        updated_at=datetime.fromisoformat(data["updated_at"])
                    )
                )
                
        # Simple statistics calculation (e.g. queue time, execution time) could be added here
        return TaskHistory(
            task_id=task_id,
            snapshots=snapshots,
            statistics=TaskStatistics()
        )
        
    async def cleanup(self, task_id: str) -> None:
        await self._cache.delete(self._snapshot_key(task_id))
        await self._cache.delete(self._history_key(task_id))
