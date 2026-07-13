"""
Caption Repository.
Provides specialized queries for Captions directly.
"""
import uuid
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.domain.models.video import CaptionTone
from app.infrastructure.repositories.base import BaseRepository, RepositoryException
from app.infrastructure.database.models.caption import CaptionORM
from app.infrastructure.database.mappers.caption_mapper import CaptionMapper


class CaptionRepository(BaseRepository):

    async def get_by_scene(self, scene_id: str) -> Dict[CaptionTone, str]:
        """Retrieves all captions for a specific scene as a Domain dictionary."""
        try:
            stmt = select(CaptionORM).where(CaptionORM.scene_id == uuid.UUID(scene_id))
            result = await self._session.execute(stmt)
            orm_captions = list(result.scalars().all())
            
            return CaptionMapper.to_domain(orm_captions)
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to get captions for scene {scene_id}: {str(e)}") from e

    async def get_by_tone(self, scene_id: str, tone: CaptionTone) -> Optional[str]:
        """Retrieves a single caption string by its specific tone."""
        try:
            stmt = (
                select(CaptionORM)
                .where(CaptionORM.scene_id == uuid.UUID(scene_id))
                .where(CaptionORM.tone == tone.value)
            )
            result = await self._session.execute(stmt)
            orm_caption = result.scalar_one_or_none()
            
            return orm_caption.text if orm_caption else None
        except SQLAlchemyError as e:
            raise RepositoryException(f"Failed to get {tone.value} caption for scene {scene_id}: {str(e)}") from e
