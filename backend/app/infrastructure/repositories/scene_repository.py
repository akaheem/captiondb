"""
Scene Repository.
Provides specialized queries for Scene entities without loading the full Video aggregate.
"""
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.domain.models.video import Scene
from app.infrastructure.repositories.base import BaseRepository, RepositoryException
from app.infrastructure.database.models.scene import SceneORM
from app.infrastructure.database.mappers.scene_mapper import SceneMapper


class SceneRepository(BaseRepository):
    
    async def get_by_id(self, scene_id: str) -> Optional[Scene]:
        """Loads a single Scene by its ID, including its Captions."""
        try:
            stmt = (
                select(SceneORM)
                .where(SceneORM.id == uuid.UUID(scene_id))
                .options(selectinload(SceneORM.captions))
            )
            result = await self._session.execute(stmt)
            orm_scene = result.scalar_one_or_none()
            
            if not orm_scene:
                return None
                
            return SceneMapper.to_domain(orm_scene)
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to get scene {scene_id}: {str(e)}") from e

    async def get_by_video(self, video_id: str) -> List[Scene]:
        """Retrieves all Scenes for a specific Video."""
        try:
            stmt = (
                select(SceneORM)
                .where(SceneORM.video_id == uuid.UUID(video_id))
                .options(selectinload(SceneORM.captions))
                .order_by(SceneORM.seconds_start.asc())
            )
            result = await self._session.execute(stmt)
            orm_scenes = result.scalars().all()
            
            return [SceneMapper.to_domain(s) for s in orm_scenes]
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to get scenes for video {video_id}: {str(e)}") from e
