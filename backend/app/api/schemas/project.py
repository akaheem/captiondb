from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.domain.models.video import VideoStatus
from app.api.schemas.upload import VideoMetadataSchema

class SceneSchema(BaseModel):
    scene_id: str
    seconds_start: float
    seconds_end: float
    title: Optional[str] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    tags: List[str] = []
    
class ProjectResponse(BaseModel):
    id: str = Field(..., description="The unique project ID (maps to Video aggregate ID).")
    project_name: str = Field(..., description="The user-defined name of the project.")
    status: VideoStatus = Field(..., description="The current processing status.")
    metadata: Optional[VideoMetadataSchema] = None
    created_at: datetime
    updated_at: datetime
    scenes: List[SceneSchema] = []

class ProjectListResponse(BaseModel):
    data: List[ProjectResponse]
    total: int
