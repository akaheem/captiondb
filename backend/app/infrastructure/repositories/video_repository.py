"""
Video Repository.
Aggregate-oriented repository for Video domain entities.
Handles saving and loading the complete Video -> Scene -> Caption tree.
"""
import uuid
from typing import List, Optional

from sqlalchemy import select, exists
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.domain.models.video import Video
from app.infrastructure.repositories.base import BaseRepository, RepositoryException
from app.infrastructure.database.models.video import VideoORM
from app.infrastructure.database.models.scene import SceneORM
from app.infrastructure.database.mappers.video_mapper import VideoMapper


class VideoRepository(BaseRepository):
    
    async def add(self, video: Video) -> None:
        """Adds a new Video aggregate to the session."""
        try:
            # The mapper recursively translates scenes and captions
            orm_video = VideoMapper.to_orm(video)
            self._session.add(orm_video)
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to add video: {str(e)}") from e

    async def get_by_id(self, video_id: str) -> Optional[Video]:
        """Loads a full Video aggregate, including all scenes and captions."""
        try:
            stmt = (
                select(VideoORM)
                .where(VideoORM.id == uuid.UUID(video_id))
                .options(
                    selectinload(VideoORM.scenes).selectinload(SceneORM.captions)
                )
            )
            result = await self._session.execute(stmt)
            orm_video = result.scalar_one_or_none()
            
            if not orm_video:
                return None
                
            return VideoMapper.to_domain(orm_video)
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to get video {video_id}: {str(e)}") from e

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Video]:
        """Retrieves a paginated list of Video aggregates."""
        try:
            stmt = (
                select(VideoORM)
                .options(
                    selectinload(VideoORM.scenes).selectinload(SceneORM.captions)
                )
                .order_by(VideoORM.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            orm_videos = result.scalars().all()
            
            return [VideoMapper.to_domain(v) for v in orm_videos]
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to get videos: {str(e)}") from e

    async def exists(self, video_id: str) -> bool:
        """Checks if a video exists without loading the full aggregate."""
        try:
            stmt = select(exists().where(VideoORM.id == uuid.UUID(video_id)))
            result = await self._session.execute(stmt)
            return result.scalar() or False
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to check existence for {video_id}: {str(e)}") from e

    async def update(self, video: Video) -> None:
        """
        Updates an existing Video aggregate.
        Merges the mapped ORM state into the active session.
        """
        try:
            orm_video = VideoMapper.to_orm(video)
            await self._session.merge(orm_video)
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to update video {video.id}: {str(e)}") from e

    async def delete(self, video_id: str) -> None:
        """Deletes a Video. Cascades down to scenes and captions via ORM configuration."""
        try:
            stmt = select(VideoORM).where(VideoORM.id == uuid.UUID(video_id))
            result = await self._session.execute(stmt)
            orm_video = result.scalar_one_or_none()
            
            if orm_video:
                await self._session.delete(orm_video)
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to delete video {video_id}: {str(e)}") from e
