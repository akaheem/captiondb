"""
Pipeline Domain Models.
Defines the final outputs and aggregations of the entire AI Pipeline.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.models.video import CaptionTone
from app.domain.models.caption import CaptionGenerationResult
from app.domain.models.vision import VisionAnalysisResult


def _now_utc():
    return datetime.now(timezone.utc)


class PipelineStatus(str, Enum):
    """Overall status of a pipeline execution."""
    SUCCESS = "Success"
    PARTIAL_SUCCESS = "Partial_Success"
    FAILED = "Failed"


@dataclass
class PipelineUsage:
    """Aggregated AI usage metrics for the entire pipeline."""
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    
    def add(self, prompt: int = 0, completion: int = 0, total: int = 0):
        self.total_prompt_tokens += prompt
        self.total_completion_tokens += completion
        self.total_tokens += total


@dataclass
class PipelineStatistics:
    """Aggregated operational statistics."""
    total_scenes: int = 0
    successful_scenes: int = 0
    failed_scenes: int = 0
    total_processing_time_seconds: float = 0.0


@dataclass
class ScenePipelineResult:
    """The complete result for a single scene processed through the AI pipeline."""
    scene_id: str
    target_tone: CaptionTone
    is_success: bool
    vision_result: Optional[VisionAnalysisResult] = None
    caption_result: Optional[CaptionGenerationResult] = None
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0


@dataclass
class VideoPipelineResult:
    """
    The final aggregated result of processing an entire video through the AI Pipeline.
    """
    video_id: str
    status: PipelineStatus
    scene_results: List[ScenePipelineResult] = field(default_factory=list)
    statistics: PipelineStatistics = field(default_factory=PipelineStatistics)
    usage: PipelineUsage = field(default_factory=PipelineUsage)
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=_now_utc)
    completed_at: Optional[datetime] = None
