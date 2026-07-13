"""
Video Analysis Domain Models.

Defines the specialized aggregate contexts needed for the Vision AI subsystem.
These contexts accumulate information stage by stage in the pipeline.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from app.domain.models.video import Video, Scene, CaptionTone, VideoMetadata
from app.domain.models.ai import AIImageContent


@dataclass
class ProcessingContext:
    """
    An accumulation root for the pipeline.
    Passed between services to hold the video and its incrementally extracted features.
    """
    video: Video
    current_stage_name: str
    extracted_frames: Dict[str, List[AIImageContent]] = field(default_factory=dict)
    ocr_texts: Dict[str, str] = field(default_factory=dict)
    # Allows attaching future context (e.g. user prompts, specific job overrides) without changing interfaces
    runtime_metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class VisionInputPackage:
    """
    The exact payload a PromptBuilder or VisionService needs to caption a specific scene.
    Prevents passing the entire Video/ProcessingContext aggregate into the AI layer.
    """
    video_id: str
    scene: Scene
    video_context: VideoMetadata
    target_tone: CaptionTone
    key_frames: List[AIImageContent]
    previous_scene_context: Optional[str] = None
    next_scene_context: Optional[str] = None


@dataclass
class VideoAnalysisPipelineResult:
    """
    The structured result of the complete Video Analysis Subsystem.
    Provides the list of ready Vision payloads, and identifies any partial failures.
    """
    is_success: bool
    packages: List[VisionInputPackage] = field(default_factory=list)
    failed_scene_ids: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
