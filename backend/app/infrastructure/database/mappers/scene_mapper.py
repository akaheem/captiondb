"""
Scene Mapper.
Translates between Domain Scene and SceneORM.
"""
import uuid
import copy
from typing import List

from app.domain.models.video import Scene
from app.infrastructure.database.models.scene import SceneORM
from app.infrastructure.database.mappers.caption_mapper import CaptionMapper


class SceneMapper:
    @staticmethod
    def to_orm(video_id: str, scene: Scene) -> SceneORM:
        """Convert a Domain Scene entity to a SceneORM entity."""
        # Defensive copy of mutable lists/dicts before sending to SQLAlchemy
        orm_scene = SceneORM(
            id=uuid.UUID(scene.scene_id),
            video_id=uuid.UUID(video_id),
            seconds_start=scene.seconds_start,
            seconds_end=scene.seconds_end,
            title=scene.title,
            thumbnail_path=scene.thumbnail_path,
            transcript=scene.transcript,
            tags=copy.deepcopy(scene.tags),
            summary=scene.summary,
            objects=copy.deepcopy(scene.objects),
            activities=copy.deepcopy(scene.activities),
            colors=copy.deepcopy(scene.colors),
            ocr_text=scene.ocr_text,
            ai_metadata=copy.deepcopy(scene.ai_metadata)
        )
        
        # Recursively map captions
        orm_scene.captions = CaptionMapper.to_orm(scene.scene_id, scene.captions)
        return orm_scene

    @staticmethod
    def to_domain(orm: SceneORM) -> Scene:
        """Convert a SceneORM entity back to a Domain Scene entity."""
        # Reconstruct the caption dictionary
        captions_dict = CaptionMapper.to_domain(orm.captions) if orm.captions else {}
        
        return Scene(
            scene_id=str(orm.id),
            seconds_start=orm.seconds_start,
            seconds_end=orm.seconds_end,
            title=orm.title,
            thumbnail_path=orm.thumbnail_path,
            transcript=orm.transcript,
            tags=copy.deepcopy(orm.tags) if orm.tags else [],
            captions=captions_dict,
            summary=orm.summary,
            objects=copy.deepcopy(orm.objects) if orm.objects else [],
            activities=copy.deepcopy(orm.activities) if orm.activities else [],
            colors=copy.deepcopy(orm.colors) if orm.colors else [],
            ocr_text=orm.ocr_text,
            ai_metadata=copy.deepcopy(orm.ai_metadata) if hasattr(orm, 'ai_metadata') and orm.ai_metadata else {}
        )
