"""
Upload API Schemas.
Pydantic definitions for HTTP requests and responses.
"""
from typing import Optional, List
from pydantic import BaseModel, Field

from app.domain.models.video import VideoStatus, VideoFormat


class VideoDimensionsSchema(BaseModel):
    width: int
    height: int


class VideoMetadataSchema(BaseModel):
    size_bytes: int
    duration_seconds: float
    fps: float
    codec: str
    resolution: str
    dimensions: VideoDimensionsSchema
    format: VideoFormat


class UploadResponse(BaseModel):
    """
    Standard response schema for successful video uploads.
    Does NOT leak internal absolute paths.
    """
    success: bool = Field(True, description="Indicates successful ingestion.")
    video_id: str = Field(..., description="The unique aggregate root ID of the ingested video.")
    project_name: str = Field(..., description="The project the video belongs to.")
    status: VideoStatus = Field(..., description="The current processing status (e.g., QUEUED).")
    metadata: Optional[VideoMetadataSchema] = Field(None, description="Intrinsic properties extracted via FFprobe.")
    errors: Optional[List[str]] = Field(None, description="Any non-fatal validation warnings.")
