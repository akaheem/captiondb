import logging
from typing import List, Tuple, Dict, Any, Optional
import copy
from app.domain.models.video import Video, VideoStatus, ProcessingState
from app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from app.core.exceptions import NotFoundException
from app.services.file import FileManagementService

logger = logging.getLogger(__name__)

class ProjectService:
    """
    Application service for managing Projects.
    In our domain, a Project maps 1:1 with a Video Aggregate Root.
    """
    
    def __init__(self, unit_of_work: AbstractUnitOfWork, file_service: FileManagementService):
        self._uow = unit_of_work
        self._file_service = file_service

    async def get_all_projects(
        self, limit: int = 100, offset: int = 0, sort_by: Optional[str] = None, status: Optional[VideoStatus] = None
    ) -> Tuple[List[Video], int]:
        """
        Retrieves a paginated list of projects (videos).
        Applies basic in-memory filtering and sorting since modifying the repository is restricted.
        """
        async with self._uow:
            # We fetch a larger chunk to allow in-memory filtering (though not perfectly paginated)
            videos = await self._uow.videos.get_all(limit=1000, offset=0)
            
            if status:
                videos = [v for v in videos if v.state.status == status]
                
            if sort_by == "created_at":
                videos.sort(key=lambda v: v.created_at, reverse=True)
            elif sort_by == "project_name":
                videos.sort(key=lambda v: v.project_name)
                
            total = len(videos)
            videos = videos[offset:offset + limit]
            
            return videos, total

    async def get_project_by_id(self, project_id: str) -> Video:
        """
        Retrieves a single project (video) by ID.
        """
        async with self._uow:
            video = await self._uow.videos.get_by_id(project_id)
            if not video:
                raise NotFoundException(f"Project with ID {project_id} not found.")
            return video

    async def delete_project(self, project_id: str) -> None:
        """
        Deletes a project (video) by ID.
        """
        async with self._uow:
            video = await self._uow.videos.get_by_id(project_id)
            if not video:
                raise NotFoundException(f"Project with ID {project_id} not found.")
                
            # Perform storage cleanup first
            try:
                await self._file_service.delete_logical_file(video.logical_path)
                if video.thumbnail_path:
                    await self._file_service.delete_logical_file(video.thumbnail_path)
                for scene in video.scenes:
                    if scene.thumbnail_path:
                        await self._file_service.delete_logical_file(scene.thumbnail_path)
            except Exception as e:
                logger.error(f"Failed to fully clean up storage for {project_id}: {str(e)}")
            
            await self._uow.videos.delete(project_id)
            await self._uow.commit()
            logger.info(f"Project {project_id} successfully deleted.")

    async def duplicate_project(self, project_id: str) -> Video:
        """
        Duplicates a project's metadata and scenes, returning the new Video aggregate.
        """
        async with self._uow:
            video = await self._uow.videos.get_by_id(project_id)
            if not video:
                raise NotFoundException(f"Project with ID {project_id} not found.")
                
            # Deep copy the domain model to sever object references
            new_video = copy.deepcopy(video)
            
            # Reset identity and update metadata
            import uuid
            from datetime import datetime, timezone
            
            new_video.id = str(uuid.uuid4())
            new_video.project_name = f"{new_video.project_name} (Copy)"
            new_video.created_at = datetime.now(timezone.utc)
            new_video.updated_at = new_video.created_at
            # A copy has not been processed — never inherit Processing/Completed state
            new_video.state = ProcessingState()
            
            # Reset all scene IDs
            for scene in new_video.scenes:
                scene.scene_id = str(uuid.uuid4())
                
            await self._uow.videos.add(new_video)
            await self._uow.commit()
            
            logger.info(f"Project {project_id} successfully duplicated to {new_video.id}.")
            return new_video

    async def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Computes project summary statistics safely away from the router layer.
        """
        video = await self.get_project_by_id(project_id)
        
        total_scenes = len(video.scenes)
        successful_scenes = sum(1 for scene in video.scenes if scene.captions or scene.summary)
        
        duration = 0.0
        if video.state.started_at and video.state.completed_at:
            duration = (video.state.completed_at - video.state.started_at).total_seconds()
            
        total_captions = sum(len(scene.captions) for scene in video.scenes)
        
        return {
            "total_scenes": total_scenes,
            "successful_scenes": successful_scenes,
            "processing_duration_seconds": duration,
            "total_captions": total_captions,
            "status": video.state.status
        }
