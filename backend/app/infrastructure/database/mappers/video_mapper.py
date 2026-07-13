"""
Video Mapper.
Translates between Domain Video and VideoORM.
Handles mapping the nested collections and flattened value objects.
"""
import uuid
import copy
from typing import Dict, Any

from app.domain.models.video import (
    Video, 
    VideoMetadata, 
    VideoDimensions, 
    ProcessingState, 
    VideoStatus, 
    VideoFormat
)
from app.infrastructure.database.models.video import VideoORM
from app.infrastructure.database.mappers.scene_mapper import SceneMapper


class VideoMapper:
    @staticmethod
    def _metadata_to_payload(metadata: VideoMetadata | None) -> Dict[str, Any] | None:
        """Flattens VideoMetadata into a JSON-compatible dictionary."""
        if not metadata:
            return None
        
        payload = {
            "size_bytes": metadata.size_bytes,
            "duration_seconds": metadata.duration_seconds,
            "fps": metadata.fps,
            "codec": metadata.codec,
            "resolution": metadata.resolution,
            "format": metadata.format.value
        }
        
        if metadata.dimensions:
            payload["dimensions"] = {
                "width": metadata.dimensions.width,
                "height": metadata.dimensions.height
            }
            
        return payload

    @staticmethod
    def _payload_to_metadata(payload: Dict[str, Any] | None) -> VideoMetadata | None:
        """Reconstructs VideoMetadata from a JSON dictionary."""
        if not payload:
            return None
            
        dimensions = None
        if "dimensions" in payload and payload["dimensions"]:
            dimensions = VideoDimensions(
                width=payload["dimensions"].get("width", 0),
                height=payload["dimensions"].get("height", 0)
            )
            
        # Parse format safely
        fmt_str = payload.get("format", VideoFormat.UNKNOWN.value)
        try:
            fmt = VideoFormat(fmt_str)
        except ValueError:
            fmt = VideoFormat.UNKNOWN
            
        return VideoMetadata(
            size_bytes=payload.get("size_bytes", 0),
            duration_seconds=payload.get("duration_seconds", 0.0),
            fps=payload.get("fps", 0.0),
            codec=payload.get("codec", "unknown"),
            resolution=payload.get("resolution", "unknown"),
            dimensions=dimensions,
            format=fmt
        )

    @staticmethod
    def to_orm(domain: Video) -> VideoORM:
        """Convert a Domain Video aggregate into a VideoORM entity."""
        orm_video = VideoORM(
            id=uuid.UUID(domain.id),
            project_name=domain.project_name,
            original_filename=domain.original_filename,
            logical_path=domain.logical_path,
            thumbnail_path=domain.thumbnail_path,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            
            # Serialize Value Objects
            metadata_payload=VideoMapper._metadata_to_payload(domain.metadata),
            
            # Flatten Processing State
            state_status=domain.state.status.value,
            state_progress_percent=domain.state.progress_percent,
            state_current_stage=domain.state.current_stage,
            state_error_message=domain.state.error_message,
            state_started_at=domain.state.started_at,
            state_completed_at=domain.state.completed_at
        )
        
        # Recursively map scenes
        orm_video.scenes = [SceneMapper.to_orm(domain.id, s) for s in domain.scenes]
        
        return orm_video

    @staticmethod
    def to_domain(orm: VideoORM) -> Video:
        """Convert a VideoORM entity back into a Domain Video aggregate."""
        # Reconstruct Processing State
        try:
            status = VideoStatus(orm.state_status)
        except ValueError:
            status = VideoStatus.FAILED
            
        state = ProcessingState(
            status=status,
            progress_percent=orm.state_progress_percent,
            current_stage=orm.state_current_stage,
            error_message=orm.state_error_message,
            started_at=orm.state_started_at,
            completed_at=orm.state_completed_at
        )
        
        # Reconstruct Video
        domain = Video(
            project_name=orm.project_name,
            original_filename=orm.original_filename,
            logical_path=orm.logical_path,
            id=str(orm.id),
            thumbnail_path=orm.thumbnail_path,
            metadata=VideoMapper._payload_to_metadata(orm.metadata_payload),
            state=state,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            scenes=[]
        )
        
        # Recursively map scenes if they are loaded
        if hasattr(orm, 'scenes') and orm.scenes is not None:
            domain.scenes = [SceneMapper.to_domain(s) for s in orm.scenes]
            
        return domain
