from typing import List, Dict, Optional
from pydantic import BaseModel
from app.domain.models.video import CaptionTone, VideoStatus
from app.api.schemas.project import SceneSchema

class SceneListResponse(BaseModel):
    data: List[SceneSchema]
    total: int

class CaptionResponse(BaseModel):
    scene_id: str
    seconds_start: float
    seconds_end: float
    captions: Dict[CaptionTone, str]

class CaptionListResponse(BaseModel):
    data: List[CaptionResponse]
    total: int

class ProjectSummaryResponse(BaseModel):
    total_scenes: int
    successful_scenes: int
    processing_duration_seconds: float
    total_captions: int
    status: VideoStatus
