"""
Video Domain Models.

Establishes the core entities and value objects for the Video domain.
Follows Domain-Driven Design (DDD) principles.
Contains strictly NO dependencies on infrastructure, storage adapters, or FastAPI.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field
import uuid


def _now_utc():
    return datetime.now(timezone.utc)

def _uuid4_str():
    return str(uuid.uuid4())


class VideoStatus(str, Enum):
    """Lifecycle statuses of a video matching frontend and processing states."""
    IDLE = "Idle"
    QUEUED = "Queued"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"


class VideoFormat(str, Enum):
    """Supported video formats."""
    MP4 = "mp4"
    MOV = "mov"
    AVI = "avi"
    WEBM = "webm"
    UNKNOWN = "unknown"


class CaptionTone(str, Enum):
    """Supported AI caption tones mirroring the frontend selection."""
    FORMAL = "formal"
    SARCASTIC = "sarcastic"
    HUMOROUS_TECH = "humorousTech"
    HUMOROUS_NON_TECH = "humorousNonTech"
    AUDIO = "audio"
    NONE = "none"


@dataclass
class VideoDimensions:
    """Value object representing video resolution dimensions."""
    width: int
    height: int


@dataclass
class VideoMetadata:
    """Immutable value object encapsulating intrinsic video properties."""
    size_bytes: int
    duration_seconds: float
    fps: float
    codec: str
    resolution: str
    dimensions: Optional[VideoDimensions] = None
    format: VideoFormat = VideoFormat.UNKNOWN


@dataclass
class ProcessingState:
    """Value object tracking the pipeline progression of a video."""
    status: VideoStatus = VideoStatus.IDLE
    progress_percent: float = 0.0
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Scene:
    """
    Entity representing a distinct temporal segment of a video.
    Contains time boundaries, visual summaries, transcripts, and generated captions.
    """
    seconds_start: float
    seconds_end: float
    scene_id: str = field(default_factory=_uuid4_str)
    title: Optional[str] = None
    thumbnail_path: Optional[str] = None
    transcript: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    captions: Dict[CaptionTone, str] = field(default_factory=dict)
    
    # AI Enrichment Fields
    summary: Optional[str] = None
    objects: List[str] = field(default_factory=list)
    activities: List[str] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)
    ocr_text: Optional[str] = None
    ai_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Video:
    """
    The Core Aggregate Root for the Video Domain.
    Represents the complete state of a user's uploaded asset.
    """
    project_name: str
    original_filename: str
    logical_path: str
    id: str = field(default_factory=_uuid4_str)
    thumbnail_path: Optional[str] = None
    metadata: Optional[VideoMetadata] = None
    state: ProcessingState = field(default_factory=ProcessingState)
    scenes: List[Scene] = field(default_factory=list)
    created_at: datetime = field(default_factory=_now_utc)
    updated_at: datetime = field(default_factory=_now_utc)
