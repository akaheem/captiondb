"""
Caption Mapper.
Maps between Domain Captions (as Dict[CaptionTone, str]) and CaptionORM models.
Since the domain uses a dictionary for captions (`captions: Dict[CaptionTone, str]`), 
the mapper converts between this dictionary and a list of CaptionORM objects.
"""
from typing import Dict, List
import uuid

from app.domain.models.video import CaptionTone
from app.infrastructure.database.models.caption import CaptionORM


class CaptionMapper:
    @staticmethod
    def to_orm(scene_id: str, captions_dict: Dict[CaptionTone, str]) -> List[CaptionORM]:
        """Convert a Domain dictionary of captions into a list of CaptionORM entities."""
        orm_list = []
        for tone, text in captions_dict.items():
            orm_list.append(
                CaptionORM(
                    scene_id=uuid.UUID(scene_id),
                    tone=tone.value,
                    text=text
                )
            )
        return orm_list

    @staticmethod
    def to_domain(captions_orm: List[CaptionORM]) -> Dict[CaptionTone, str]:
        """Convert a list of CaptionORM entities back into a Domain dictionary."""
        domain_dict = {}
        for caption in captions_orm:
            try:
                tone = CaptionTone(caption.tone)
                domain_dict[tone] = caption.text
            except ValueError:
                # If an unknown tone exists in the database, we can skip or map to a fallback.
                pass
        return domain_dict
